import logging 
from utils.pip_utils import price_to_pips, pips_to_price

class PullbackQualifier:
    def __init__(self, min_candles=2, max_candles=5, min_depth=0.25, max_depth=0.65, ema_buffer=2.5):
        """
        Pullback qualification with BALANCED settings optimized for real EURUSD 70-tick data
        
        Changes from original:
        - min_depth: 0.3 → 0.25 (allow slightly shallower pullbacks)
        - max_depth: 0.6 → 0.65 (allow slightly deeper pullbacks)  
        - ema_buffer: 1.5 → 2.5 (more tolerance for EMA distance)
        - wick_tolerance: 2.0 → 4.0 pips (realistic for Feb 2026 market conditions)
        """
        self.min_candles = min_candles
        self.max_candles = max_candles
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.ema_buffer = ema_buffer

    def qualify(self, pb_candles, impulse, indicators):
        n = len(pb_candles)
        if not (self.min_candles <= n <= self.max_candles):
            logging.debug(f"PB: candle count {n} out of range [{self.min_candles}-{self.max_candles}]")
            return False

        impulse_range = impulse["high"] - impulse["low"]
        if impulse_range == 0:
            return False

        if impulse["direction"] == "BUY":
            current_low = min(c["low"] for c in pb_candles)
            depth = (impulse["high"] - current_low) / impulse_range

            # UPDATED: Structure check with 4-pip tolerance (was 2 pips)
            # Real market data shows 3-8 pip overshoots are normal in 70-tick charts
            max_pb_high = max(c["high"] for c in pb_candles)
            wick_tolerance = pips_to_price(4.0)  # CHANGED from 2.0
            
            if max_pb_high > impulse["high"] + wick_tolerance:
                overshoot = price_to_pips(max_pb_high - impulse["high"])
                logging.info(f"PB Qualification: excessive new high (+{overshoot:.1f} pips)")
                return False
            
            # But BODY must not exceed impulse high
            max_pb_close = max(c["close"] for c in pb_candles)
            if max_pb_close > impulse["high"]:
                logging.info(f"PB Qualification: body close above impulse high")
                return False
                
        else:  # SELL
            current_high = max(c["high"] for c in pb_candles)
            depth = (current_high - impulse["low"]) / impulse_range

            # UPDATED: 4-pip tolerance for SELL setups too
            min_pb_low = min(c["low"] for c in pb_candles)
            wick_tolerance = pips_to_price(4.0)  # CHANGED from 2.0
            
            if min_pb_low < impulse["low"] - wick_tolerance:
                overshoot = price_to_pips(impulse["low"] - min_pb_low)
                logging.info(f"PB Qualification: excessive new low (-{overshoot:.1f} pips)")
                return False
            
            # But BODY must not exceed impulse low
            min_pb_close = min(c["close"] for c in pb_candles)
            if min_pb_close < impulse["low"]:
                logging.info(f"PB Qualification: body close below impulse low")
                return False

        # Depth check - UPDATED ranges (was 30-60%, now 25-65%)
        if not (self.min_depth <= depth <= self.max_depth):
            logging.info(f"PB Qualification: depth {depth:.1%} out of range [{self.min_depth:.0%}-{self.max_depth:.0%}]")
            return False

        # EMA Interaction - UPDATED buffer (was 1.5 pips, now 2.5 pips)
        ema = indicators.get("ema20")
        if ema:
            near_ema = False
            for c in pb_candles:
                # Touch
                if c["low"] <= ema <= c["high"]:
                    near_ema = True
                    break
                # Within buffer
                dist = min(abs(c["low"] - ema), abs(c["high"] - ema))
                if price_to_pips(dist) <= self.ema_buffer:
                    near_ema = True
                    break

            if not near_ema:
                closest_dist = min([min(abs(c["low"] - ema), abs(c["high"] - ema)) for c in pb_candles])
                logging.info(f"PB Qualification: not near EMA (closest: {price_to_pips(closest_dist):.1f} pips)")
                return False

        # Body Behavior
        pb_avg_body = sum(abs(c["close"] - c["open"]) for c in pb_candles) / n
        impulse_avg_body = impulse.get("avg_body", 0)
        
        if impulse_avg_body > 0 and pb_avg_body >= 0.7 * impulse_avg_body:
            logging.info(f"PB Qualification: body too large (pb:{pb_avg_body:.5f} vs imp:{impulse_avg_body:.5f})")
            return False

        logging.info(f"✓ Pullback qualified: {n} candles, {depth:.1%} depth")
        return True