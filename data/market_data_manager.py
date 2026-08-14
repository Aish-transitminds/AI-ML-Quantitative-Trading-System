"""Market data manager — orchestrates tick flow, subscriptions, and filters.

This is the central coordinator that:
1. Receives raw ticks from the broker WebSocket
2. Normalizes and stores ticks
3. Builds bars from ticks
4. Manages tiered subscriptions (LTP mode -> Full mode)
5. Evaluates LTP and liquidity filters
6. Provides data access to the rest of the application

Subscription Strategy (Angel One 1,000 token limit):
    Boot -> Subscribe all NSE equities in LTP mode (Mode 1)
    Filter -> Identify stocks with 30 <= LTP <= 500
    Upgrade -> Subscribe qualifying stocks in Full mode (Mode 3)
    Rescan -> Periodically re-evaluate, adjust subscriptions
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Dict, Set, Optional, List, Any

from broker.base import MarketDataProvider
from config import settings
from data.models import MarketTick, Bar, StockScreenResult
from data.instrument_manager import InstrumentManager
from data.tick_store import TickStore
from data.bar_builder import BarBuilder
from storage.database import DatabaseManager
from utils.logging_config import get_logger
from utils.helpers import get_ist_now

logger = get_logger("data.market_data_manager")


class MarketDataManager:
    """Central market data orchestrator."""
    
    def __init__(
        self,
        broker: MarketDataProvider,
        db: DatabaseManager,
    ):
        self.broker = broker
        self.db = db
        self.instruments = InstrumentManager(db)
        self.tick_store = TickStore()
        self.bar_builder = BarBuilder()
        
        # Shared state for dashboard
        self._screen_results: Dict[str, StockScreenResult] = {}
        self._lock = threading.Lock()
        
        # Subscription management
        self._full_mode_tokens: Set[str] = set()  # Currently in Mode 3
        self._last_rescan_time = 0.0
        
        # Status
        self._running = False
        self._tick_count = 0
        self._last_tick_time: Optional[datetime] = None
    
    def initialize(self) -> bool:
        """Initialize the data pipeline.
        
        1. Load instruments from broker
        2. Set up WebSocket callbacks
        3. Start subscriptions
        """
        try:
            # Load instrument universe
            instruments = self.broker.get_instruments("NSE")
            if not instruments:
                logger.error("No instruments loaded from broker")
                return False
            
            self.instruments.load_instruments(instruments)
            logger.info(f"Initialized with {self.instruments.total_count} NSE instruments")
            
            # Set up tick and disconnect callbacks
            self.broker.set_on_tick_callback(self._on_tick)
            self.broker.set_on_disconnect_callback(self._on_disconnect)
            
            self._running = True
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def start_streaming(self) -> None:
        """Start market data streaming.
        
        Subscribes to all instruments in LTP mode initially,
        then upgrades qualifying stocks to Full mode.
        """
        if not self._running:
            logger.error("Manager not initialized")
            return
        
        # Start WebSocket
        self.broker.start_websocket()
        
        # Wait for connection
        time.sleep(2)
        
        # Subscribe all tokens in LTP mode (Mode 1)
        all_tokens = self.instruments.get_all_tokens()
        max_subs = self.broker.get_max_subscriptions()
        
        # Subscribe in batches
        batch_size = min(50, max_subs)
        for i in range(0, min(len(all_tokens), max_subs), batch_size):
            batch = all_tokens[i:i + batch_size]
            self.broker.subscribe(batch, mode=MarketDataProvider.MODE_LTP)
            time.sleep(0.1)  # Small delay between batches
        
        logger.info(f"Subscribed {min(len(all_tokens), max_subs)} tokens in LTP mode")
    
    def _on_tick(self, tick: MarketTick) -> None:
        """Process incoming tick from broker WebSocket.
        
        This is called from the WebSocket thread. Must be fast.
        """
        try:
            self._tick_count += 1
            self._last_tick_time = tick.timestamp
            
            # 1. Store tick
            self.tick_store.add_tick(tick)
            
            # 2. Update instrument manager with latest LTP
            self.instruments.update_ltp(tick.token, tick.ltp)
            
            # 3. Update liquidity if we have bid/ask data (Mode 3)
            if tick.bid_quantity > 0 or tick.ask_quantity > 0:
                self.instruments.update_liquidity(
                    tick.token, tick.bid_quantity, tick.ask_quantity
                )
            
            # 4. Build bars
            self.bar_builder.process_tick(tick)
            
            # 5. Update screen result
            self._update_screen_result(tick)
            
            # 6. Periodic rescan for subscription upgrades
            now = time.time()
            if now - self._last_rescan_time > settings.SUBSCRIPTION_RESCAN_INTERVAL:
                self._rescan_subscriptions()
                self._last_rescan_time = now
            
            # 7. Periodic tick persistence
            if self.tick_store.should_persist():
                # Do this in a separate thread to avoid blocking
                threading.Thread(
                    target=self.tick_store.persist_to_parquet,
                    daemon=True
                ).start()
                
        except Exception as e:
            logger.error(f"Error processing tick for {tick.symbol}: {e}")
    
    def _update_screen_result(self, tick: MarketTick) -> None:
        """Update the screening result for a symbol."""
        with self._lock:
            symbol = tick.symbol
            
            if symbol not in self._screen_results:
                self._screen_results[symbol] = StockScreenResult(
                    symbol=symbol,
                    token=tick.token,
                )
            
            result = self._screen_results[symbol]
            result.ltp = tick.ltp
            result.bid_price = tick.bid_price
            result.bid_quantity = tick.bid_quantity
            result.ask_price = tick.ask_price
            result.ask_quantity = tick.ask_quantity
            result.last_update = tick.timestamp
    
    def _rescan_subscriptions(self) -> None:
        """Re-evaluate which stocks should be in Full mode.
        
        Upgrade: Stocks passing LTP filter -> Mode 3
        Downgrade: Stocks no longer passing -> back to Mode 1
        """
        try:
            ltp_qualified = self.instruments.get_ltp_qualified_tokens()
            currently_full = self._full_mode_tokens.copy()
            
            # Tokens to upgrade to Mode 3
            to_upgrade = ltp_qualified - currently_full
            # Tokens to downgrade back to Mode 1
            to_downgrade = currently_full - ltp_qualified
            
            if to_downgrade:
                self.broker.unsubscribe(list(to_downgrade), mode=MarketDataProvider.MODE_FULL)
                self._full_mode_tokens -= to_downgrade
            
            if to_upgrade:
                # Check subscription limits
                max_subs = self.broker.get_max_subscriptions()
                available = max_subs - len(self._full_mode_tokens)
                upgrade_list = list(to_upgrade)[:available]
                
                if upgrade_list:
                    self.broker.subscribe(upgrade_list, mode=MarketDataProvider.MODE_FULL)
                    self._full_mode_tokens.update(upgrade_list)
            
            if to_upgrade or to_downgrade:
                logger.info(
                    f"Subscription rescan: +{len(to_upgrade)} upgraded, "
                    f"-{len(to_downgrade)} downgraded, "
                    f"{len(self._full_mode_tokens)} in Full mode"
                )
                
        except Exception as e:
            logger.error(f"Subscription rescan failed: {e}")
    
    def get_screen_results(self) -> Dict[str, StockScreenResult]:
        """Get current screening results (thread-safe copy)."""
        with self._lock:
            return dict(self._screen_results)
    
    def get_qualified_results(self) -> Dict[str, StockScreenResult]:
        """Get only liquidity-qualified screening results."""
        qualified_tokens = self.instruments.get_liquidity_qualified_tokens()
        with self._lock:
            return {
                sym: result for sym, result in self._screen_results.items()
                if result.token in qualified_tokens
            }
    
    def _on_disconnect(self, reason: str) -> None:
        """Handle broker disconnect and attempt reconnect."""
        if not self._running:
            return
            
        logger.warning(f"Broker disconnected ({reason}). Attempting reconnect in 5 seconds...")
        time.sleep(5)
        
        try:
            # We must re-establish WebSocket
            self.broker.start_websocket()
            time.sleep(2)
            
            # Re-subscribe tokens we were already tracking
            if self._full_mode_tokens:
                # Mode 3
                tokens = list(self._full_mode_tokens)
                for i in range(0, len(tokens), 50):
                    self.broker.subscribe(tokens[i:i + 50], mode=MarketDataProvider.MODE_FULL)
                    time.sleep(0.1)
                logger.info(f"Re-subscribed {len(tokens)} tokens to Mode 3")
            
            # Also re-subscribe Mode 1 for tokens not in full mode
            ltp_tokens = set(self.instruments.get_all_tokens()) - self._full_mode_tokens
            if ltp_tokens:
                tokens = list(ltp_tokens)
                for i in range(0, len(tokens), 50):
                    self.broker.subscribe(tokens[i:i + 50], mode=MarketDataProvider.MODE_LTP)
                    time.sleep(0.1)
                logger.info(f"Re-subscribed {len(tokens)} tokens to Mode 1")
                
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            
    @property
    def status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'running': self._running,
            'broker_connected': self.broker.is_connected(),
            'broker_name': self.broker.get_broker_name(),
            'total_instruments': self.instruments.total_count,
            'ltp_qualified': self.instruments.ltp_qualified_count,
            'liquidity_qualified': self.instruments.liquidity_qualified_count,
            'tick_count': self._tick_count,
            'last_tick_time': self._last_tick_time,
            'full_mode_subscriptions': len(self._full_mode_tokens),
            'mode': settings.MODE,
        }
    
    def stop(self) -> None:
        """Stop the data pipeline."""
        self._running = False
        try:
            self.tick_store.persist_to_parquet()
        except Exception as e:
            logger.error(f"Error persisting ticks on shutdown: {e}")
        self.broker.disconnect()
        logger.info("Market data manager stopped")
