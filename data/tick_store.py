"""Tick storage manager with rolling in-memory buffer and Parquet persistence.

Maintains a fixed-size rolling window of recent ticks per symbol for
real-time calculations (ETQ, LTQ averages, etc.) and periodically
persists to Parquet files for historical analysis.

IMPORTANT DISTINCTIONS:
- Volume: Cumulative quantity traded during the day (from broker)
- LTQ: Quantity of the most recent trade/tick
- ETQ: Sum of LTQ over a rolling time window (calculated, not from broker)
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Deque

import pandas as pd
import numpy as np

from config import settings
from data.models import MarketTick
from utils.logging_config import get_logger
from utils.helpers import safe_divide

logger = get_logger("data.tick_store")


class TickStore:
    """Thread-safe in-memory tick storage with rolling windows.
    
    For each symbol, maintains a deque of recent MarketTick objects
    capped at TICK_BUFFER_MAX_MINUTES of data.
    
    Provides efficient computation of:
    - ETQ (Exchange Traded Quantity) over rolling windows
    - Average LTP over rolling windows
    - LTQ statistics
    """
    
    def __init__(self):
        self._ticks: Dict[str, Deque[MarketTick]] = defaultdict(
            lambda: deque(maxlen=50000)  # Safety cap
        )
        self._lock = threading.Lock()
        self._last_persist_time = time.time()
        self._tick_count = 0
    
    def add_tick(self, tick: MarketTick) -> None:
        """Add a new tick to the store.
        
        Validates and deduplicates before storing.
        """
        if not tick.validate():
            logger.debug(f"Invalid tick rejected: {tick.symbol}")
            return
        
        with self._lock:
            symbol = tick.symbol
            buffer = self._ticks[symbol]
            
            # Check for duplicate timestamp (same symbol + same timestamp)
            if buffer and buffer[-1].timestamp == tick.timestamp and buffer[-1].ltp == tick.ltp:
                return  # Skip duplicate
            
            buffer.append(tick)
            self._tick_count += 1
            
            # Trim old ticks beyond buffer limit
            cutoff = tick.timestamp - timedelta(minutes=settings.TICK_BUFFER_MAX_MINUTES)
            while buffer and buffer[0].timestamp < cutoff:
                buffer.popleft()
    
    def get_ticks(self, symbol: str, minutes: Optional[int] = None) -> List[MarketTick]:
        """Get recent ticks for a symbol.
        
        Args:
            symbol: Trading symbol.
            minutes: If provided, only return ticks within last N minutes.
            
        Returns:
            List of MarketTick objects, ordered by timestamp.
        """
        with self._lock:
            buffer = self._ticks.get(symbol, deque())
            if not buffer:
                return []
            
            if minutes is None:
                return list(buffer)
            
            cutoff = buffer[-1].timestamp - timedelta(minutes=minutes)
            return [t for t in buffer if t.timestamp >= cutoff]
    
    def get_latest_tick(self, symbol: str) -> Optional[MarketTick]:
        """Get the most recent tick for a symbol."""
        with self._lock:
            buffer = self._ticks.get(symbol, deque())
            return buffer[-1] if buffer else None
    
    def calculate_etq(self, symbol: str, minutes: int) -> int:
        """Calculate Exchange Traded Quantity over a rolling window.
        
        ETQ = sum of LTQ for all ticks in the specified time window.
        
        This is NOT the same as daily volume. ETQ is the sum of
        individual trade quantities (LTQ) within a specific time period.
        
        Args:
            symbol: Trading symbol.
            minutes: Rolling window in minutes.
            
        Returns:
            Sum of LTQ values in the window.
        """
        ticks = self.get_ticks(symbol, minutes)
        return sum(t.ltq for t in ticks)
    
    def calculate_avg_ltp(self, symbol: str, minutes: int) -> float:
        """Calculate average LTP over a rolling window.
        
        Robust to irregular tick frequency — uses simple mean of all
        observed LTP values within the window.
        
        Args:
            symbol: Trading symbol.
            minutes: Rolling window in minutes.
            
        Returns:
            Mean LTP value, or 0.0 if no ticks.
        """
        ticks = self.get_ticks(symbol, minutes)
        if not ticks:
            return 0.0
        return sum(t.ltp for t in ticks) / len(ticks)
    
    def calculate_ltq_stats(self, symbol: str, minutes: int) -> Dict[str, float]:
        """Calculate LTQ statistics over a rolling window.
        
        Returns:
            Dict with keys: avg, std, median, count
        """
        ticks = self.get_ticks(symbol, minutes)
        if not ticks:
            return {'avg': 0.0, 'std': 0.0, 'median': 0.0, 'count': 0}
        
        ltq_values = [t.ltq for t in ticks if t.ltq > 0]
        if not ltq_values:
            return {'avg': 0.0, 'std': 0.0, 'median': 0.0, 'count': 0}
        
        arr = np.array(ltq_values, dtype=np.float64)
        return {
            'avg': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'median': float(np.median(arr)),
            'count': len(ltq_values),
        }
    
    def get_price_return(self, symbol: str, minutes: int) -> float:
        """Calculate price return over a time window.
        
        return = (current_ltp - ltp_N_minutes_ago) / ltp_N_minutes_ago
        
        Args:
            symbol: Trading symbol.
            minutes: Lookback period.
            
        Returns:
            Percentage return (e.g., 0.02 for 2%), or 0.0 if insufficient data.
        """
        ticks = self.get_ticks(symbol, minutes)
        if len(ticks) < 2:
            return 0.0
        
        current_ltp = ticks[-1].ltp
        old_ltp = ticks[0].ltp
        
        return safe_divide(current_ltp - old_ltp, old_ltp, 0.0)
    
    def get_symbols(self) -> List[str]:
        """Get all symbols with stored ticks."""
        with self._lock:
            return list(self._ticks.keys())
    
    def get_tick_count(self, symbol: Optional[str] = None) -> int:
        """Get number of stored ticks."""
        with self._lock:
            if symbol:
                return len(self._ticks.get(symbol, deque()))
            return self._tick_count
    
    def persist_to_parquet(self, symbol: Optional[str] = None) -> None:
        """Persist tick data to Parquet files.
        
        Saves ticks to data_store/raw_ticks/{symbol}_{date}.parquet
        """
        with self._lock:
            symbols = [symbol] if symbol else list(self._ticks.keys())
        
        for sym in symbols:
            ticks = self.get_ticks(sym)
            if not ticks:
                continue
            
            try:
                records = []
                for t in ticks:
                    records.append({
                        'timestamp': t.timestamp,
                        'symbol': t.symbol,
                        'ltp': t.ltp,
                        'ltq': t.ltq,
                        'volume': t.volume,
                        'bid_price': t.bid_price,
                        'bid_quantity': t.bid_quantity,
                        'ask_price': t.ask_price,
                        'ask_quantity': t.ask_quantity,
                        'total_buy_quantity': t.total_buy_quantity,
                        'total_sell_quantity': t.total_sell_quantity,
                    })
                
                df = pd.DataFrame(records)
                date_str = datetime.now().strftime('%Y%m%d')
                safe_sym = sym.replace('-', '_').replace(' ', '_')
                filepath = settings.RAW_TICKS_DIR / f"{safe_sym}_{date_str}.parquet"
                df.to_parquet(filepath, index=False, engine='pyarrow')
                
            except Exception as e:
                logger.error(f"Failed to persist ticks for {sym}: {e}")
        
        self._last_persist_time = time.time()
    
    def should_persist(self) -> bool:
        """Check if it's time to persist ticks."""
        return (time.time() - self._last_persist_time) >= settings.TICK_PERSIST_INTERVAL_SECONDS
    
    def clear_symbol(self, symbol: str) -> None:
        """Clear all ticks for a symbol."""
        with self._lock:
            if symbol in self._ticks:
                del self._ticks[symbol]
