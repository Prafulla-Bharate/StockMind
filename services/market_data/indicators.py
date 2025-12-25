import numpy as np
import pandas as pd
try:
    import talib as ta
    _USING_TALIB = True
except Exception:
    # Fall back to the pure-Python `ta` package if TA-Lib is not available
    import ta as _ta_fallback
    _USING_TALIB = False
from apps.market.models import Stock, StockPrice, TechnicalIndicator
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicatorCalculator:
    """Calculate technical indicators"""

    def __init__(self):
        pass

    def calculate_indicators(self, symbol, lookback_days=200):
        """Calculate all technical indicators for a stock"""
        try:
            stock = Stock.objects.get(symbol=symbol)

            # -----------------------------------------------
            # CHANGE 1: Use timestamps correctly + iterator()
            # -----------------------------------------------
            prices_qs = (
                StockPrice.objects
                .filter(stock=stock)
                .order_by('timestamp')
                .values('timestamp', 'close', 'high', 'low', 'volume')
            )
            df = pd.DataFrame(list(prices_qs)[-lookback_days:])
            if len(df) < 50:
                logger.warning(f"Not enough data for {symbol}")
                return None

            # Convert to numpy arrays
            close = df['close'].astype(float).values
            high = df['high'].astype(float).values
            low = df['low'].astype(float).values
            volume = df['volume'].astype(float).values

            indicators = {}

            # Moving Averages
            if _USING_TALIB:
                indicators['sma_20'] = ta.SMA(close, timeperiod=20)
                indicators['sma_50'] = ta.SMA(close, timeperiod=50)
                indicators['sma_200'] = ta.SMA(close, timeperiod=200)
                indicators['ema_12'] = ta.EMA(close, timeperiod=12)
                indicators['ema_26'] = ta.EMA(close, timeperiod=26)

                # RSI
                indicators['rsi_14'] = ta.RSI(close, timeperiod=14)

                # MACD
                macd, macd_signal, macd_hist = ta.MACD(
                    close,
                    fastperiod=12,
                    slowperiod=26,
                    signalperiod=9
                )
                indicators['macd'] = macd
                indicators['macd_signal'] = macd_signal
                indicators['macd_histogram'] = macd_hist

                # Bollinger Bands
                upper, middle, lower = ta.BBANDS(
                    close,
                    timeperiod=20,
                    nbdevup=2,
                    nbdevdn=2
                )
                indicators['bollinger_upper'] = upper
                indicators['bollinger_middle'] = middle
                indicators['bollinger_lower'] = lower

                # ATR
                indicators['atr_14'] = ta.ATR(high, low, close, timeperiod=14)

                # OBV
                indicators['obv'] = ta.OBV(close, volume)
            else:
                # Use `ta` package (pure Python) as fallback - operates on pandas Series
                close_s = pd.Series(close)
                high_s = pd.Series(high)
                low_s = pd.Series(low)
                vol_s = pd.Series(volume)

                indicators['sma_20'] = _ta_fallback.trend.sma_indicator(close_s, window=20).to_numpy()
                indicators['sma_50'] = _ta_fallback.trend.sma_indicator(close_s, window=50).to_numpy()
                indicators['sma_200'] = _ta_fallback.trend.sma_indicator(close_s, window=200).to_numpy()
                indicators['ema_12'] = _ta_fallback.trend.ema_indicator(close_s, window=12).to_numpy()
                indicators['ema_26'] = _ta_fallback.trend.ema_indicator(close_s, window=26).to_numpy()

                indicators['rsi_14'] = _ta_fallback.momentum.rsi(close_s, window=14).to_numpy()

                macd_obj = _ta_fallback.trend.MACD(close_s, window_slow=26, window_fast=12, window_sign=9)
                indicators['macd'] = macd_obj.macd().to_numpy()
                indicators['macd_signal'] = macd_obj.macd_signal().to_numpy()
                indicators['macd_histogram'] = macd_obj.macd_diff().to_numpy()

                bb = _ta_fallback.volatility.BollingerBands(close_s, window=20, window_dev=2)
                indicators['bollinger_upper'] = bb.bollinger_hband().to_numpy()
                indicators['bollinger_middle'] = bb.bollinger_mavg().to_numpy()
                indicators['bollinger_lower'] = bb.bollinger_lband().to_numpy()

                atr_obj = _ta_fallback.volatility.AverageTrueRange(high_s, low_s, close_s, window=14)
                indicators['atr_14'] = atr_obj.average_true_range().to_numpy()

                obv_obj = _ta_fallback.volume.OnBalanceVolumeIndicator(close_s, vol_s)
                indicators['obv'] = obv_obj.on_balance_volume().to_numpy()

            latest_timestamp = df.iloc[-1]['timestamp']
            indicator_data = {'timestamp': latest_timestamp}

            # ---------------------------------------------------------
            # CHANGE 2: NaN-safe saving for all indicators automatically
            # ---------------------------------------------------------
            for key, arr in indicators.items():
                last_val = arr[-1]
                if not np.isnan(last_val):
                    indicator_data[key] = float(last_val)

            TechnicalIndicator.objects.update_or_create(
                stock=stock,
                timestamp=latest_timestamp,
                defaults=indicator_data
            )

            return indicator_data

        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            return None

    def calculate_support_resistance(self, symbol, lookback_days=100):
        """Calculate support and resistance levels"""
        try:
            stock = Stock.objects.get(symbol=symbol)

            # ------------------------------------
            # CHANGE 3: Fetch latest N rows properly
            # ------------------------------------
            prices = (
                StockPrice.objects
                .filter(stock=stock)
                .order_by('-timestamp')[:lookback_days]
            )

            if len(prices) < 20:
                return None

            df = pd.DataFrame(list(prices.values('close', 'high', 'low')))

            highs = df['high'].astype(float).values
            lows = df['low'].astype(float).values

            resistance = np.percentile(highs, 95)
            support = np.percentile(lows, 5)

            return {
                'resistance': float(resistance),
                'support': float(support)
            }

        except Exception as e:
            logger.error(f"Error calculating support/resistance for {symbol}: {e}")
            return None
