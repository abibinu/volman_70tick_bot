import numpy as np

class PerformanceReport:
    def __init__(self, trades):
        self.trades = trades

    def calculate_metrics(self):
        if not self.trades:
            return {"status": "No trades executed"}
        profits = [t["profit"] for t in self.trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]
        total_trades = len(self.trades)
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        cumulative_profit = np.cumsum(profits)
        peak = np.maximum.accumulate(cumulative_profit)
        peak = np.maximum(peak, 0)
        drawdowns = peak - cumulative_profit
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        return {"total_trades": total_trades, "win_rate": win_rate * 100, "profit_factor": profit_factor, "total_net_profit": sum(profits), "max_drawdown": max_drawdown, "avg_win": avg_win, "avg_loss": avg_loss, "expectancy": (win_rate * avg_win) + ((1 - win_rate) * avg_loss)}

    def display(self):
        metrics = self.calculate_metrics()
        print("\n" + "="*40 + "\n📊 BACKTEST PERFORMANCE REPORT\n" + "="*40)
        if "status" in metrics:
            print(metrics["status"])
        else:
            print(f"Total Trades:    {metrics['total_trades']}\nWin Rate:        {metrics['win_rate']:.2f}%\nProfit Factor:   {metrics['profit_factor']:.2f}\nTotal Net Profit:{metrics['total_net_profit']:.2f} pips\nMax Drawdown:    {metrics['max_drawdown']:.2f} pips\nExpectancy:      {metrics['expectancy']:.2f} pips/trade\nAvg Win/Loss:    {metrics['avg_win']:.2f} / {metrics['avg_loss']:.2f}")
        print("="*40 + "\n")
