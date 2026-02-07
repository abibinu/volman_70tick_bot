from data.mt5_adapter import MT5Adapter
from data.tick_engine import TickCandleEngine
from indicators.indicator_engine import IndicatorEngine

mt5 = MT5Adapter()
mt5.connect()

tick_engine = TickCandleEngine(70)
ind_engine = IndicatorEngine()

while True:
    tick = mt5.get_tick("EURUSD")
    if not tick:
        continue

    candle = tick_engine.process_tick(tick)
    if candle:
        indicators = ind_engine.update(candle)
        print(candle["index"], indicators)
