import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_ticks(symbol="EURUSD", days=1, start_price=1.1000):
    np.random.seed(42)
    num_ticks = 30000 * days
    ticks = []
    current_price = start_price
    current_time = datetime.now() - timedelta(days=days)
    for i in range(num_ticks):
        if 5000 <= i < 5500:
            change = 0.00002
        elif 5500 <= i < 5700:
            change = -0.00001
        elif 5700 <= i < 5800:
            change = 0.00003
        else:
            cycle_pos = i % 2000
            if cycle_pos < 500:
                change = np.random.normal(0.000002, 0.00001)
            elif cycle_pos < 700:
                change = np.random.normal(-0.000005, 0.000008)
            elif cycle_pos < 1200:
                change = np.random.normal(0.000004, 0.000012)
            else:
                change = np.random.normal(0, 0.000015)
        current_price += change
        spread = 0.00005 + np.random.uniform(0, 0.00003)
        ticks.append({"symbol": symbol, "bid": current_price, "ask": current_price + spread, "spread": spread, "timestamp": current_time + timedelta(milliseconds=i * 500)})
    return ticks
