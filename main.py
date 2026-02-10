import time
import logging
from data.mt5_adapter import MT5Adapter
from data.tick_engine import TickCandleEngine
from indicators.indicator_engine import IndicatorEngine
from strategy.strategy_engine import StrategyEngine
from risk.risk_engine import RiskEngine
from execution.execution_engine import ExecutionEngine
from utils.time_utils import is_session_active
from utils.pip_utils import price_to_pips

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

def main():
    symbol = "EURUSD"
    mt5 = MT5Adapter()

    if not mt5.connect():
        logging.error("Failed to connect to MT5. Exiting.")
        return

    tick_engine = TickCandleEngine(70)
    ind_engine = IndicatorEngine()
    risk_engine = RiskEngine()
    strategy_engine = StrategyEngine(risk_engine)
    exec_engine = ExecutionEngine(mt5)

    logging.info("Volman 70-Tick Scalper Bot Started")
    logging.info(f"Symbol: {symbol} | Tick per candle: 70")

    try:
        while True:
            # 1. Session Filter
            if not is_session_active():
                if risk_engine.trades_this_session > 0:
                    logging.info("Session ended. Resetting daily stats.")
                    risk_engine.reset_session()
                time.sleep(30)
                continue

            # 2. Fetch Tick
            tick = mt5.get_tick(symbol)
            if not tick:
                logging.warning("Failed to fetch tick. Retrying...")
                time.sleep(0.1)
                continue

            # ✅ FIXED: Changed from 1.0 to 0.8 to avoid dead zone
            # Previously: spread > 1.0 blocked loop, but trades only executed if spread <= 0.8
            # Now: spread > 0.8 blocks everything (consistent with execution threshold)
            # 3. Spread Filter
            spread_pips = price_to_pips(tick["spread"], symbol)
            if spread_pips > 0.8:
                # Skip this tick if spread too high
                time.sleep(0.1)
                continue

            # 4. Tick Candle Generation
            candle = tick_engine.process_tick(tick)
            if candle:
                logging.info(f"New 70-tick candle: {candle['index']} | Close: {candle['close']:.5f}")

                # 5. Indicators Update
                indicators = ind_engine.update(candle)

                # 6. Strategy Logic
                signal = strategy_engine.process_candle(candle, indicators)

                if signal:
                    if risk_engine.can_trade():
                        # ✅ FIXED: Removed redundant spread check (already filtered above)
                        # Previously checked spread <= 0.8 here, but we already blocked if > 0.8
                        ticket = exec_engine.execute_signal(signal, symbol)
                        if ticket > 0:
                            risk_engine.register_new_trade()
                    else:
                        logging.info("Signal ignored due to risk limits.")

                # 7. Update active trades candle count
                exec_engine.update_candles_count()

            # 8. Real-time Trade Management (BE, Time Stop)
            exec_engine.manage_trades(symbol, risk_engine)

            time.sleep(0.001)  # High frequency loop

    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Critical error: {e}", exc_info=True)
    finally:
        # ✅ FIXED: Added cleanup call before shutdown
        exec_engine.cleanup_closed_trades(risk_engine)
        mt5.shutdown()
        logging.info("MT5 connection closed. Goodbye.")

if __name__ == "__main__":
    main()