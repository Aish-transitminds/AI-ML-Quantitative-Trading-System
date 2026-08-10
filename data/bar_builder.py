"""Bar builder: Aggregates real-time ticks into 1-minute OHLCV bars.

These bars serve as the input for SMMA calculation.

Methodology:
- Each bar covers one calendar minute (e.g., 09:15:00 to 09:15:59)
- Bars are built incrementally as ticks arrive
- When a new minute starts, the previous bar is finalized
- Historical bars can be loaded from the broker's historical API

Why 1-minute bars:
- Standard intraday analysis timeframe
- Fine enough to capture short-term crossovers
- Coarse enough to be computationally efficient
- Consistent with typical quant analysis practices
"""
from __future__ import annotations

import threading
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable

from data.models import MarketTick, Bar
from utils.logging_config import get_logger

logger = get_logger("data.bar_builder")


def _bar_timestamp(dt: datetime) -> datetime:
    """Truncate datetime to the start of its minute."""
    return dt.replace(second=0, microsecond=0)


class BarBuilder:
    """Builds 1-minute bars from incoming ticks.
    
    For each symbol, maintains:
    - A list of completed (historical) bars
    - The current (in-progress) bar
    
    When a new minute starts, the current bar is finalized
    and added to history. Callbacks are triggered.
    """
    
    def __init__(self, max_bars: int = 500):
        self._bars: Dict[str, List[Bar]] = defaultdict(list)
        self._current_bar: Dict[str, Bar] = {}
        self._max_bars = max_bars
        self._on_bar_complete: Optional[Callable[[str, Bar], None]] = None
        self._lock = threading.Lock()
    
    def set_on_bar_complete(self, callback: Callable[[str, Bar], None]) -> None:
        """Register callback for when a bar is completed.
        
        Args:
            callback: Function(symbol, bar) called when a bar finalizes.
        """
        self._on_bar_complete = callback
    
    def process_tick(self, tick: MarketTick) -> Optional[Bar]:
        """Process a new tick and update bars.
        
        Args:
            tick: Incoming market tick.
            
        Returns:
            The completed bar if a new minute started, else None.
        """
        symbol = tick.symbol
        tick_bar_ts = _bar_timestamp(tick.timestamp)
        completed_bar = None
        
        with self._lock:
            current = self._current_bar.get(symbol)
            
            if current is None:
                # First tick for this symbol — start new bar
                self._current_bar[symbol] = Bar(
                    timestamp=tick_bar_ts,
                    symbol=symbol,
                    open=tick.ltp,
                    high=tick.ltp,
                    low=tick.ltp,
                    close=tick.ltp,
                )
                self._current_bar[symbol].update(tick)
                
            elif tick_bar_ts > current.timestamp:
                # New minute — finalize current bar
                current.is_complete = True
                self._bars[symbol].append(current)
                completed_bar = current
                
                # Trim history
                if len(self._bars[symbol]) > self._max_bars:
                    self._bars[symbol] = self._bars[symbol][-self._max_bars:]
                
                # Start new bar
                self._current_bar[symbol] = Bar(
                    timestamp=tick_bar_ts,
                    symbol=symbol,
                    open=tick.ltp,
                    high=tick.ltp,
                    low=tick.ltp,
                    close=tick.ltp,
                )
                self._current_bar[symbol].update(tick)
                
            else:
                # Same minute — update current bar
                current.update(tick)
        
        if completed_bar and self._on_bar_complete:
            try:
                self._on_bar_complete(symbol, completed_bar)
            except Exception as e:
                logger.error(f"Error in on_bar_complete callback for {symbol}: {e}")
        
        return completed_bar
    
    def load_historical_bars(self, symbol: str, bars: List[Bar]) -> None:
        """Load historical bars for SMMA warm-up.
        
        Args:
            symbol: Trading symbol.
            bars: List of historical bars, ordered by timestamp.
        """
        with self._lock:
            for bar in bars:
                bar.is_complete = True
            self._bars[symbol] = bars[-self._max_bars:]
        
        logger.info(f"Loaded {len(bars)} historical bars for {symbol}")
    
    def get_bars(self, symbol: str, count: Optional[int] = None) -> List[Bar]:
        """Get completed bars for a symbol.
        
        Args:
            symbol: Trading symbol.
            count: If provided, return only the last N bars.
            
        Returns:
            List of completed bars, ordered by timestamp.
        """
        with self._lock:
            bars = self._bars.get(symbol, [])
            if count:
                return bars[-count:]
            return list(bars)
    
    def get_current_bar(self, symbol: str) -> Optional[Bar]:
        """Get the in-progress bar for a symbol."""
        with self._lock:
            return self._current_bar.get(symbol)
    
    def get_close_prices(self, symbol: str, count: Optional[int] = None) -> List[float]:
        """Get close prices from completed bars."""
        bars = self.get_bars(symbol, count)
        return [b.close for b in bars]
    
    def bar_count(self, symbol: str) -> int:
        """Get number of completed bars for a symbol."""
        with self._lock:
            return len(self._bars.get(symbol, []))
