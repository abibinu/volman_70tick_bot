import unittest
from strategy.trend import TrendAnalyzer
from strategy.impulse import ImpulseDetector
from strategy.pullback import PullbackQualifier
from strategy.structure import StructureMonitor
from strategy.entry import EntryTrigger
from risk.risk_engine import RiskEngine
from utils.pip_utils import pips_to_price

class TestStrategyModules(unittest.TestCase):
    def setUp(self):
        self.trend = TrendAnalyzer(ema_slope_threshold=1.5)
        self.impulse = ImpulseDetector(min_size=8, min_candles=5)
        self.pullback = PullbackQualifier(min_depth=0.3, max_depth=0.6)
        self.structure = StructureMonitor(ema_buffer_pips=1.0)
        self.entry = EntryTrigger(buffer_pips=0.3)
        self.risk = RiskEngine()

    def test_trend_qualify(self):
        # Uptrend: Close > EMA, Slope > 1.5 pips
        candle = {"close": 1.1020, "high": 1.1025, "low": 1.1015, "index": 20}
        indicators = {"ema20": 1.1010, "ema20_slope": 0.0002} # 2 pips
        self.assertTrue(self.trend.qualify_uptrend(candle, indicators))

        # Downtrend: Close < EMA, Slope < -1.5 pips
        candle = {"close": 1.0980, "high": 1.0985, "low": 1.0975, "index": 20}
        indicators = {"ema20": 1.0990, "ema20_slope": -0.0002} # -2 pips
        self.assertTrue(self.trend.qualify_downtrend(candle, indicators))

    def test_trend_hh_ll(self):
        # Fill history with 20 candles that DON'T make a higher high
        for i in range(20):
            candle = {"close": 1.1020, "high": 1.1025, "low": 1.1015, "index": i}
            indicators = {"ema20": 1.1010, "ema20_slope": 0.0002}
            res = self.trend.qualify_uptrend(candle, indicators)
            if i < 19:
                self.assertTrue(res) # Still qualifying because history < 20
            else:
                self.assertFalse(res) # History is 20, and no HH in last 10 vs prev 10

    def test_impulse_detect(self):
        # 5 candles, 10 pips move
        candles = []
        for i in range(5):
            candles.append({
                "open": 1.1000 + i*0.0002,
                "close": 1.1002 + i*0.0002,
                "high": 1.1003 + i*0.0002,
                "low": 1.1000 + i*0.0002,
                "index": i
            })
        res = self.impulse.detect(candles)
        self.assertIsNotNone(res)
        self.assertEqual(res["direction"], "UP")
        self.assertGreaterEqual(res["size"], 8.0)

    def test_pullback_qualify(self):
        impulse = {"direction": "UP", "high": 1.1010, "low": 1.1000, "avg_body": 0.0002}
        # Pullback 3 pips deep (30%)
        # Bodies should be < 0.7 * 0.0002 = 0.00014
        pb_candles = [
            {"open": 1.1010, "close": 1.10095, "high": 1.1010, "low": 1.1009},
            {"open": 1.1009, "close": 1.10085, "high": 1.1009, "low": 1.1007}
        ]
        indicators = {"ema20": 1.1007} # Touching EMA
        self.assertTrue(self.pullback.qualify(pb_candles, impulse, indicators))

    def test_risk_calculations(self):
        self.risk.register_new_trade()
        self.assertEqual(self.risk.trades_this_session, 1)
        
        # ✅ FIXED: Corrected SL/TP calculation test
        # Entry: 1.1010, PB extreme (low): 1.1005
        entry = 1.1010
        pb_extreme = 1.1005
        
        sl, tp = self.risk.calculate_sl_tp("UP", entry, pb_extreme)
        
        # SL should be: pb_extreme - 0.5 pips = 1.1005 - 0.00005 = 1.10045
        expected_sl = pb_extreme - pips_to_price(0.5)
        self.assertAlmostEqual(sl, expected_sl, places=5)
        
        # TP should be: entry + (risk * 1.2)
        # Risk = entry - sl = 1.1010 - 1.10045 = 0.00055
        # TP = 1.1010 + (0.00055 * 1.2) = 1.1010 + 0.00066 = 1.10166
        risk = entry - sl
        expected_tp = entry + (risk * 1.2)
        self.assertAlmostEqual(tp, expected_tp, places=5)
        
        # Verify RR is 1.2
        actual_rr = (tp - entry) / (entry - sl)
        self.assertAlmostEqual(actual_rr, 1.2, places=2)

if __name__ == "__main__":
    unittest.main()