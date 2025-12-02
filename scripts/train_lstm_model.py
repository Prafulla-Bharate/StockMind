import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
import os
from datetime import datetime

class LSTMModelTrainer:
    """Train LSTM model on stock data"""
    
    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        
    def fetch_training_data(self, symbols, period='5y'):
        """
        Fetch historical data for multiple stocks
        More data = better model
        """
        print(f"Fetching data for {len(symbols)} stocks...")
        all_data = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if len(hist) > 100:
                    hist['symbol'] = symbol
                    all_data.append(hist[['Open', 'High', 'Low', 'Close', 'Volume']])
                    print(f"✓ {symbol}: {len(hist)} days")
                else:
                    print(f"✗ {symbol}: Not enough data")
                    
            except Exception as e:
                print(f"✗ {symbol}: Error - {e}")
                continue
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal data points: {len(combined_df)}")
        
        return combined_df
    
    def prepare_data(self, df):
        """Prepare data for LSTM training"""
        print("\nPreparing data...")
        
        # Use all OHLCV features
        features = ['Open', 'High', 'Low', 'Close', 'Volume']
        data = df[features].values
        
        # Normalize data
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            y.append(scaled_data[i, 3])  # Predict Close price
        
        X, y = np.array(X), np.array(y)
        
        print(f"Sequences created: {len(X)}")
        print(f"Input shape: {X.shape}")
        
        return X, y
    
    def build_model(self, input_shape):
        """Build LSTM architecture"""
        print("\nBuilding model...")
        
        model = Sequential([
            # First LSTM layer
            LSTM(100, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            
            # Second LSTM layer
            LSTM(100, return_sequences=True),
            Dropout(0.2),
            
            # Third LSTM layer
            LSTM(100, return_sequences=False),
            Dropout(0.2),
            
            # Dense layers
            Dense(50, activation='relu'),
            Dropout(0.2),
            Dense(1)  # Output: predicted price
        ])
        
        # Compile model
        model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        print(model.summary())
        
        return model
    
    def train(self, X, y, epochs=50, batch_size=32, validation_split=0.2):
        """Train the model"""
        print("\nTraining model...")
        
        # Build model
        self.model = self.build_model((X.shape[1], X.shape[2]))
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        
        checkpoint = ModelCheckpoint(
            'models/lstm_model_best.keras',
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
        
        # Train
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop, checkpoint],
            verbose=1
        )
        
        return history
    
    def save_model(self, model_path='models/lstm_model.keras', scaler_path='models/lstm_scaler.pkl'):
        """Save trained model and scaler"""
        print(f"\nSaving model to {model_path}...")
        
        os.makedirs('models', exist_ok=True)
        
        # Save model
        self.model.save(model_path)
        
        # Save scaler
        joblib.dump(self.scaler, scaler_path)
        
        print("✓ Model saved successfully!")
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        print("\nEvaluating model...")
        
        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        
        print(f"Test Loss (MSE): {loss:.4f}")
        print(f"Test MAE: {mae:.4f}")
        
        return loss, mae

# ============================================================================
# MAIN TRAINING SCRIPT
# ============================================================================

def main():
    """Main training function"""
    
    print("=" * 60)
    print("LSTM Stock Price Prediction Model Training")
    print("=" * 60)
    
    # 1. Define stocks to train on (more stocks = better generalization)
    training_stocks = [
        # Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
        
        # Finance
        'JPM', 'BAC', 'WFC', 'GS', 'MS',
        
        # Consumer
        'WMT', 'HD', 'MCD', 'NKE', 'SBUX',
        
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO',
        
        # Energy
        'XOM', 'CVX', 'COP',
        
        # Industrial
        'BA', 'CAT', 'GE', 'MMM',
        
        # Add more for better model (recommend 50-100 stocks)
    ]
    
    print(f"\nTraining on {len(training_stocks)} stocks")
    print(f"This will download ~5 years of data for each stock\n")
    
    # 2. Initialize trainer
    trainer = LSTMModelTrainer(sequence_length=60)
    
    # 3. Fetch training data
    df = trainer.fetch_training_data(training_stocks, period='5y')
    
    if len(df) < 1000:
        print("\n⚠️ Warning: Not enough data. Add more stocks or use longer period.")
        return
    
    # 4. Prepare data
    X, y = trainer.prepare_data(df)
    
    # 5. Split data (80% train, 20% test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print(f"\nTrain set: {len(X_train)} sequences")
    print(f"Test set: {len(X_test)} sequences")
    
    # 6. Train model
    history = trainer.train(
        X_train, y_train,
        epochs=50,  # Increase for better results
        batch_size=32,
        validation_split=0.2
    )
    
    # 7. Evaluate
    trainer.evaluate(X_test, y_test)
    
    # 8. Save model
    trainer.save_model(
        model_path='models/lstm_model.keras',
        scaler_path='models/lstm_scaler.pkl'
    )
    
    print("\n" + "=" * 60)
    print("✓ Training Complete!")
    print("=" * 60)
    print("\nFiles saved:")
    print("  - models/lstm_model.h5 (trained model)")
    print("  - models/lstm_scaler.pkl (data scaler)")
    print("\nYou can now use these files in your backend!")
    print("Just copy them to your backend's models/ folder.")

if __name__ == '__main__':
    main()
