# 📖 Volman 70-Tick Scalper: Complete Guide

This document provides a comprehensive overview of the bot's architecture, strategy implementation, and how to use the built-in backtesting system.

---

## 🏛 Architecture Overview

The bot is designed with a modular, state-machine architecture to ensure production stability and easy testing.

### Core Components
- **`main.py`**: The central orchestrator. It manages the connection to MetaTrader 5, filters for trading sessions (IST), and runs the high-frequency tick loop.
- **`strategy/`**: Contains the decoupled logic for identifying trades.
  - `trend.py`: EMA-based trend qualification (Slope & HH/LL).
  - `impulse.py`: Detects strong institutional moves (Impulse legs).
  - `pullback.py`: Qualifies shallow retracements (2-5 candles).
  - `entry.py`: Handles the "Tick Break" logic for precise entries.
- **`data/`**:
  - `mt5_adapter.py`: Production bridge to MetaTrader 5.
  - `tick_engine.py`: Converts raw price ticks into 70-tick candles.
- **`execution/`**: Manages active positions, including Break-Even adjustments (+5 pips) and the 15-candle Time Stop.
- **`backtest/`**: A simulation suite that allows testing without a live MT5 connection.

---

## 🧠 Strategy Workflow

The bot operates as a **State Machine** with three primary phases:

1.  **SEARCHING**:
    *   The bot looks for a confirmed trend (Price vs 20 EMA + Slope > 1.5 pips).
    *   It waits for an **Impulse Leg** (8+ pips move over 5+ candles with high body dominance).
2.  **WAITING_PULLBACK**:
    *   Once an impulse is detected, it waits for a "healthy" pullback (30-60% retracement).
    *   The pullback must touch or come very close to the 20 EMA.
    *   Structure is monitored: a breakout of the impulse high/low during pullback invalidates the setup.
3.  **WAITING_TRIGGER**:
    *   Once qualified, the bot enters **Tick-Level Monitoring**.
    *   It does NOT wait for a candle to close. It monitors every price tick.
    *   **Entry**: If price breaks the pullback's extreme (plus a 0.3 pip buffer), a market order is sent immediately.

---

## 🧪 Backtesting System

You can verify profitability and logic using the synthetic backtester.

### How to Run
```bash
python3 run_backtest.py
```

### How it Works
1.  **Mock Adapter**: `backtest/mock_adapter.py` replaces the real MetaTrader 5 API. It simulates order fills, SL/TP hits, and spread.
2.  **Data Generation**: `backtest/generate_test_data.py` creates realistic EURUSD tick sequences, including trending phases and pullbacks.
3.  **Performance Report**: After the run, the bot prints a detailed report including:
    *   Win Rate (%)
    *   Profit Factor (Gross Win / Gross Loss)
    *   Max Drawdown (in pips)
    *   Expectancy (average pips per trade)

---

## 🛠 Production Readiness & Safety

The bot includes several features specifically for live deployment:

-   **Session Filter**: Automatically pauses outside London (12:30-16:30 IST) and NY (18:30-21:30 IST) sessions.
-   **Spread Filter**: Blocks trades if the broker spread exceeds 0.8 pips.
-   **News Filter**: Blocks setup initiation 15 minutes before/after high-impact news events.
-   **Heartbeat Monitor**: Detects if the broker's tick feed has frozen and attempts to reconnect.
-   **Risk Limits**:
    *   Max 5 trades per session.
    *   Halts trading after 3 consecutive losses.
    *   Structural Stop Loss (fallback to 6.5 pips if structure is too tight).

---

## 📈 Tips for Increasing Profitability

1.  **Parameter Tuning**: In `strategy/strategy_engine.py`, you can fine-tune the `min_size` of impulses or the `ema_slope_threshold`.
2.  **News Updates**: Regularly update the `news_events` list in `utils/news_filter.py` with times from an economic calendar.
3.  **Spread Monitoring**: If trading a pair with higher spreads (like GBPUSD), increase the spread limit in `main.py`.

---

**Warning**: Trading involves risk. Always run the bot on a Demo account for at least 2 weeks before moving to live funds.
