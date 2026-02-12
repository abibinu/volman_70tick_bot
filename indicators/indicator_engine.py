import logging

class IndicatorEngine:
    def __init__(self, ema_period=20, slope_lookback=6, range_lookback=20):  # FIXED: Reduced from 11 to 6
        self.ema_period = ema_period
        self.slope_lookback = slope_lookback
        self.range_lookback = range_lookback

        self.candles = []
        self.ema_values = []
        
        # Memory management
        self.max_history = 100

    def update(self, candle: dict):
        self.candles.append(candle)
        
        # Memory management - keep only recent candles
        if len(self.candles) > self.max_history:
            self.candles.pop(0)

        close = candle["close"]

        # EMA calculation
        if not self.ema_values:
            ema = close
        else:
            alpha = 2 / (self.ema_period + 1)
            ema = alpha * close + (1 - alpha) * self.ema_values[-1]

        self.ema_values.append(ema)
        
        # Memory management for EMA values
        if len(self.ema_values) > self.max_history:
            self.ema_values.pop(0)

        # FIXED: EMA slope calculation with fallback for early candles
        ema_slope = None
        if len(self.ema_values) >= self.slope_lookback:
            # Current EMA minus EMA from slope_lookback candles ago
            ema_slope = ema - self.ema_values[-self.slope_lookback]
        elif len(self.ema_values) >= 3:
            # Fallback: use shorter lookback during warmup
            lookback = len(self.ema_values)
            ema_slope = ema - self.ema_values[-lookback]
            logging.debug(f"Using fallback slope: {lookback} candles (need {self.slope_lookback})")

        # Average range (volatility filter)
        avg_range = None
        if len(self.candles) >= self.range_lookback:
            ranges = [
                c["high"] - c["low"]
                for c in self.candles[-self.range_lookback:]
            ]
            avg_range = sum(ranges) / len(ranges)
        elif len(self.candles) >= 5:
            # Fallback: use shorter range during warmup
            ranges = [c["high"] - c["low"] for c in self.candles]
            avg_range = sum(ranges) / len(ranges)

        return {
            "ema20": ema,
            "ema20_slope": ema_slope,
            "avg_range": avg_range
        }