import pandas as pd
from typing import List


class LSTMPredictor:
    """Lightweight LSTM predictor stub.

    This is a simple, deterministic fallback used for development and testing.
    Replace with a real trained model for production use.
    """

    def __init__(self):
        pass

    def predict(self, df: pd.DataFrame, steps: int = 30) -> List[float]:
        """Return a naive prediction: repeat the last close price for `steps`.

        Args:
            df: DataFrame with at least a `close` column.
            steps: Number of future steps to predict.

        Returns:
            List of predicted close prices (floats).
        """
        if 'close' not in df.columns or len(df) == 0:
            return []

        try:
            last_close = float(df['close'].iloc[-1])
        except Exception:
            return []

        return [last_close for _ in range(steps)]
