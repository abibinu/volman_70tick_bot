from backtest.generate_test_data import generate_synthetic_ticks
from backtest.replay_engine import ReplayEngine
import logging

def main():
    logging.basicConfig(level=logging.WARNING)
    ticks = generate_synthetic_ticks(days=2)
    engine = ReplayEngine(symbol="EURUSD")
    report = engine.run(ticks)
    report.display()

if __name__ == "__main__":
    main()
