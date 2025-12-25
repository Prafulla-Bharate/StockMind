import pandas as pd
from typing import List


class LSTMPredictor:
    """Lightweight deterministic forecaster.

    Uses recent average daily return to project a smooth forward path. This is
    a placeholder until a trained model is plugged in but at least produces a
    trending curve instead of a flat line.
    """

    def __init__(self):
        pass

    def predict(self, df: pd.DataFrame, steps: int = 30) -> List[float]:
        """Project prices using recent average return (no randomness)."""
        if 'close' not in df.columns or len(df) == 0:
            return []

        # Clean series and ensure we have enough history
        closes = pd.Series(df['close']).astype(float).dropna()
        if len(closes) < 10:
            return []

        returns = closes.pct_change().dropna()
        if returns.empty:
            return []

        lookback = min(60, len(returns))
        recent_returns = returns.tail(lookback)
        avg_return = recent_returns.mean()

        try:
            last_close = float(closes.iloc[-1])
        except Exception:
            return []

        if last_close <= 0:
            return []

        forecast = []
        for step in range(1, steps + 1):
            # Deterministic geometric growth based on observed drift
            projected = last_close * ((1 + avg_return) ** step)
            if projected <= 0:
                projected = last_close  # prevent negative/zero prices
            forecast.append(float(projected))

        return forecast
