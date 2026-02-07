from datetime import datetime


class TickCandleEngine:
    def __init__(self, ticks_per_candle: int = 70):
        self.ticks_per_candle = ticks_per_candle
        self.reset()
        self.candle_index = 0

    def reset(self):
        self.tick_count = 0
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.timestamp_open = None

    def process_tick(self, tick: dict):
        price = (tick["bid"] + tick["ask"]) / 2

        if self.tick_count == 0:
            self.open = price
            self.high = price
            self.low = price
            self.timestamp_open = tick["timestamp"]

        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price

        self.tick_count += 1

        if self.tick_count >= self.ticks_per_candle:
            candle = {
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume_ticks": self.tick_count,
                "index": self.candle_index,
                "timestamp_open": self.timestamp_open,
                "timestamp_close": tick["timestamp"]
            }

            self.candle_index += 1
            self.reset()
            return candle

        return None
