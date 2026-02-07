class IndicatorEngine:
    def __init__(self, ema_period=20, slope_lookback=10, range_lookback=20):
        self.ema_period = ema_period
        self.slope_lookback = slope_lookback
        self.range_lookback = range_lookback

        self.candles = []
        self.ema_values = []

    def update(self, candle: dict):
        self.candles.append(candle)

        close = candle["close"]

        # EMA calculation
        if not self.ema_values:
            ema = close
        else:
            alpha = 2 / (self.ema_period + 1)
            ema = alpha * close + (1 - alpha) * self.ema_values[-1]

        self.ema_values.append(ema)

        # EMA slope
        ema_slope = None
        if len(self.ema_values) > self.slope_lookback:
            ema_slope = ema - self.ema_values[-self.slope_lookback]

        # Average range (volatility filter)
        avg_range = None
        if len(self.candles) >= self.range_lookback:
            ranges = [
                c["high"] - c["low"]
                for c in self.candles[-self.range_lookback:]
            ]
            avg_range = sum(ranges) / len(ranges)

        return {
            "ema20": ema,
            "ema20_slope": ema_slope,
            "avg_range": avg_range
        }
