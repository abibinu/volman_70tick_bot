import time
import logging
from datetime import datetime
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

class VolmanTradingBot:
    """
    ✅ PRODUCTION READY: Volman 70-Tick Scalping Bot
    
    Features:
    - Automatic MT5 connection recovery
    - Tick heartbeat monitoring
    - Session-aware trading
    - Risk management
    - Comprehensive error handling
    - Periodic statistics logging
    """
    
    def __init__(self, symbol="EURUSD", volume=0.1):
        self.symbol = symbol
        self.volume = volume
        
        # MT5 Connection
        self.mt5 = MT5Adapter()
        
        # Trading Components
        self.tick_engine = None
        self.ind_engine = None
        self.risk_engine = None
        self.strategy_engine = None
        self.exec_engine = None
        
        # Connection Monitoring
        self.last_tick_time = None
        self.connection_errors = 0
        self.max_connection_errors = 3
        
        # Statistics
        self.session_start_time = None
        self.last_stats_log = None
        
    def ensure_mt5_connected(self):
        """Monitor and restore MT5 connection if lost"""
        if not self.mt5.connected:
            logging.warning("⚠️ MT5 disconnected. Attempting reconnection...")
            
            for attempt in range(self.max_connection_errors):
                logging.info(f"Reconnection attempt {attempt + 1}/{self.max_connection_errors}")
                
                if self.mt5.connect():
                    logging.info("✅ MT5 reconnected successfully")
                    self.connection_errors = 0
                    return True
                
                time.sleep(5)
            
            logging.error("❌ Failed to reconnect to MT5 after multiple attempts")
            return False
        
        return True
    
    def check_tick_heartbeat(self):
        """Detect if ticks have stopped coming (connection issue)"""
        if self.last_tick_time is None:
            return True
        
        time_since_last_tick = (datetime.now() - self.last_tick_time).total_seconds()
        
        if time_since_last_tick > 30:  # No tick for 30 seconds
            logging.warning(f"⚠️ No ticks received for {time_since_last_tick:.0f} seconds - possible connection issue")
            return False
        
        return True
    
    def log_statistics(self):
        """Log current session statistics"""
        logging.info("=" * 60)
        logging.info("📊 SESSION STATISTICS")
        logging.info(f"Symbol: {self.symbol}")
        logging.info(f"Trades this session: {self.risk_engine.trades_this_session}")
        logging.info(f"Consecutive losses: {self.risk_engine.consecutive_losses}")
        logging.info(f"Strategy state: {self.strategy_engine.state}")
        
        # Tick engine stats
        tick_stats = self.tick_engine.get_stats()
        logging.info(f"Total ticks processed: {tick_stats['total_ticks_processed']}")
        logging.info(f"Total candles generated: {tick_stats['total_candles_generated']}")
        logging.info(f"Current candle: {tick_stats['current_candle_ticks']}/{self.tick_engine.ticks_per_candle} ticks "
                   f"({self.tick_engine.get_completion_percentage():.1f}%)")
        
        # Active trades
        if self.exec_engine.active_trades:
            logging.info(f"Active trades: {len(self.exec_engine.active_trades)}")
            logging.info(self.exec_engine.get_active_trades_summary())
        else:
            logging.info("Active trades: None")
        
        if self.session_start_time:
            uptime = (datetime.now() - self.session_start_time).total_seconds() / 60
            logging.info(f"Session uptime: {uptime:.1f} minutes")
        
        logging.info("=" * 60)
    
    def initialize(self):
        """Initialize all bot components"""
        logging.info("=" * 70)
        logging.info("🚀 VOLMAN 70-TICK SCALPING BOT - PRODUCTION MODE")
        logging.info("=" * 70)
        logging.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("")
        
        # Connect to MT5
        if not self.mt5.connect():
            logging.error("❌ Failed to connect to MT5. Exiting.")
            return False
        
        logging.info("✅ MT5 connected successfully")
        logging.info("")
        
        # Initialize components
        self.tick_engine = TickCandleEngine(70)
        self.ind_engine = IndicatorEngine()
        self.risk_engine = RiskEngine(
            max_trades_session=5,
            max_consecutive_losses=3
        )
        self.strategy_engine = StrategyEngine(self.risk_engine)
        self.exec_engine = ExecutionEngine(self.mt5)
        
        # Configuration
        logging.info("⚙️ CONFIGURATION")
        logging.info(f"Symbol: {self.symbol}")
        logging.info(f"Position size: {self.volume} lots")
        logging.info(f"Ticks per candle: 70")
        logging.info(f"Max spread: 0.8 pips")
        logging.info(f"Session times (IST): London 12:30-16:30, NY 18:30-21:30")
        logging.info(f"Max trades per session: {self.risk_engine.max_trades_session}")
        logging.info(f"Max consecutive losses: {self.risk_engine.max_consecutive_losses}")
        logging.info("")
        
        # Show loaded positions
        if self.exec_engine.active_trades:
            logging.info("📊 EXISTING POSITIONS DETECTED")
            logging.info(self.exec_engine.get_active_trades_summary())
            logging.info("")
        
        logging.info("=" * 70)
        logging.info("✅ Initialization complete. Starting main loop...")
        logging.info("=" * 70)
        logging.info("")
        
        self.session_start_time = datetime.now()
        self.last_stats_log = datetime.now()
        
        return True
    
    def run(self):
        """Main bot trading loop"""
        if not self.initialize():
            return
        
        try:
            iteration = 0
            last_session_check = datetime.now()
            
            while True:
                iteration += 1
                
                # === Periodic Health Checks ===
                
                # Every 100 iterations (~0.1 seconds): Check connection
                if iteration % 100 == 0:
                    if not self.ensure_mt5_connected():
                        logging.error("Cannot restore MT5 connection. Waiting 30s...")
                        time.sleep(30)
                        continue
                    
                    if not self.check_tick_heartbeat():
                        logging.warning("Tick heartbeat failed. Checking connection...")
                        self.ensure_mt5_connected()
                
                # Every 5 minutes: Log statistics
                if (datetime.now() - self.last_stats_log).total_seconds() > 300:
                    self.log_statistics()
                    self.last_stats_log = datetime.now()
                
                # === 1. Session Filter ===
                if not is_session_active():
                    # Check once per minute if session ended
                    if (datetime.now() - last_session_check).total_seconds() > 60:
                        if self.risk_engine.trades_this_session > 0:
                            logging.info("=" * 60)
                            logging.info("⏰ Session ended. Resetting daily statistics.")
                            logging.info(f"Final count: {self.risk_engine.trades_this_session} trades")
                            logging.info("=" * 60)
                            self.risk_engine.reset_session()
                        last_session_check = datetime.now()
                    
                    time.sleep(30)
                    continue
                
                # === 2. Fetch Tick ===
                try:
                    tick = self.mt5.get_tick(self.symbol)
                except Exception as e:
                    logging.error(f"Error fetching tick: {e}")
                    tick = None
                
                if not tick:
                    self.connection_errors += 1
                    
                    if self.connection_errors >= self.max_connection_errors:
                        logging.error(f"Multiple tick fetch failures ({self.connection_errors}). Checking connection...")
                        self.ensure_mt5_connected()
                        self.connection_errors = 0
                    
                    time.sleep(0.1)
                    continue
                
                # Reset error counter on successful tick
                self.connection_errors = 0
                self.last_tick_time = datetime.now()
                
                # === 3. Spread Filter ===
                spread_pips = price_to_pips(tick["spread"], self.symbol)
                if spread_pips > 0.8:
                    time.sleep(0.1)
                    continue
                
                # === 4. Process Tick → Build Candle ===
                candle = self.tick_engine.process_tick(tick)
                
                if candle:
                    logging.info(f"📊 New 70-tick candle #{candle['index']} | "
                               f"O:{candle['open']:.5f} H:{candle['high']:.5f} "
                               f"L:{candle['low']:.5f} C:{candle['close']:.5f}")
                    
                    # === 5. Update Indicators ===
                    indicators = self.ind_engine.update(candle)
                    
                    # === 6. Strategy Logic ===
                    signal = self.strategy_engine.process_candle(candle, indicators)
                    
                    if signal:
                        # Check risk limits
                        if self.risk_engine.can_trade():
                            logging.info("=" * 60)
                            logging.info(f"🎯 SIGNAL GENERATED: {signal['direction']}")
                            logging.info(f"Entry: {signal['entry_price']:.5f}")
                            logging.info(f"SL: {signal['sl']:.5f} | TP: {signal['tp']:.5f}")
                            
                            try:
                                ticket = self.exec_engine.execute_signal(signal, self.symbol, self.volume)
                                if ticket > 0:
                                    self.risk_engine.register_new_trade()
                                    logging.info(f"✅ Trade #{ticket} opened successfully")
                                else:
                                    logging.error("❌ Failed to execute signal")
                            except Exception as e:
                                logging.error(f"Error executing trade: {e}")
                            
                            logging.info("=" * 60)
                        else:
                            reasons = []
                            if self.risk_engine.trades_this_session >= self.risk_engine.max_trades_session:
                                reasons.append(f"max trades ({self.risk_engine.max_trades_session})")
                            if self.risk_engine.consecutive_losses >= self.risk_engine.max_consecutive_losses:
                                reasons.append(f"max losses ({self.risk_engine.max_consecutive_losses})")
                            
                            logging.info(f"⛔ Signal ignored: {', '.join(reasons)}")
                    
                    # === 7. Update Candle Count for Active Trades ===
                    self.exec_engine.update_candles_count()
                
                # === 8. Manage Active Trades ===
                try:
                    self.exec_engine.manage_trades(self.symbol, self.risk_engine)
                except Exception as e:
                    logging.error(f"Error managing trades: {e}")
                
                # High-frequency loop
                time.sleep(0.001)
        
        except KeyboardInterrupt:
            logging.info("\n" + "=" * 70)
            logging.info("🛑 Bot stopped by user (Ctrl+C)")
            logging.info("=" * 70)
        
        except Exception as e:
            logging.error(f"💥 CRITICAL ERROR: {e}", exc_info=True)
        
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Clean shutdown procedure"""
        logging.info("")
        logging.info("=" * 70)
        logging.info("🧹 SHUTTING DOWN...")
        logging.info("=" * 70)
        
        try:
            # Cleanup closed trades
            if self.exec_engine:
                self.exec_engine.cleanup_closed_trades(self.risk_engine)
                
                # Warn about open positions
                if self.exec_engine.active_trades:
                    logging.warning("⚠️ WARNING: Bot shutting down with OPEN POSITIONS!")
                    logging.warning("")
                    logging.warning(self.exec_engine.get_active_trades_summary())
                    logging.warning("")
                    logging.warning("These positions will continue to run in MT5")
                    logging.warning("Restart the bot to resume management")
            
            # Final statistics
            if self.risk_engine:
                logging.info(f"Final session statistics: {self.risk_engine.trades_this_session} trades executed")
            
            # Close MT5
            if self.mt5:
                self.mt5.shutdown()
                logging.info("✅ MT5 connection closed")
            
            if self.session_start_time:
                total_uptime = (datetime.now() - self.session_start_time).total_seconds() / 60
                logging.info(f"Total uptime: {total_uptime:.1f} minutes")
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
        
        logging.info("=" * 70)
        logging.info("👋 Goodbye!")
        logging.info("=" * 70)


def main():
    """Entry point"""
    bot = VolmanTradingBot(
        symbol="EURUSD",
        volume=0.1  # Adjust position size as needed
    )
    bot.run()


if __name__ == "__main__":
    main()