"""SMMA crossover detection state machine.

Detects every valid crossover between SMMA(fast) and SMMA(slow):

BUY crossover:
    Previous: SMMA_fast <= SMMA_slow
    Current:  SMMA_fast > SMMA_slow

SELL crossover:
    Previous: SMMA_fast >= SMMA_slow
    Current:  SMMA_fast < SMMA_slow

IMPORTANT: A signal is generated ONLY on state transition.
Repeated ticks where SMMA_fast > SMMA_slow do NOT generate 
multiple BUY signals. Only the first crossing generates a signal.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, Optional, Callable, List
from enum import Enum

from config import settings
from data.models import SignalType, CrossoverSignal
from indicators.smma import SMMACalculator
from utils.logging_config import get_logger

logger = get_logger("signals.crossover")


class CrossoverState(Enum):
    """State of SMMA relationship."""
    UNKNOWN = "UNKNOWN"  # Not enough data yet
    BULLISH = "BULLISH"  # SMMA_fast > SMMA_slow
    BEARISH = "BEARISH"  # SMMA_fast < SMMA_slow
    EQUAL = "EQUAL"      # SMMA_fast == SMMA_slow (rare)


class CrossoverDetector:
    """Detects SMMA crossovers for a single symbol.
    
    Maintains SMMA calculators and previous state to detect
    state transitions (crossovers).
    """
    
    def __init__(self, fast_period: int = None, slow_period: int = None):
        self.fast_period = fast_period or settings.SMMA_FAST_PERIOD
        self.slow_period = slow_period or settings.SMMA_SLOW_PERIOD
        self.smma_fast = SMMACalculator(self.fast_period)
        self.smma_slow = SMMACalculator(self.slow_period)
        self._prev_state = CrossoverState.UNKNOWN
        self._signal_history: List[CrossoverSignal] = []
    
    def update(self, price: float, timestamp: datetime) -> Optional[CrossoverSignal]:
        """Update with a new bar close price and check for crossover.
        
        Args:
            price: Bar closing price.
            timestamp: Bar timestamp.
            
        Returns:
            CrossoverSignal if a crossover occurred, else None.
        """
        fast_val = self.smma_fast.update(price)
        slow_val = self.smma_slow.update(price)
        
        # Need both SMMA values to detect crossovers
        if fast_val is None or slow_val is None:
            return None
        
        # Determine current state
        if fast_val > slow_val:
            current_state = CrossoverState.BULLISH
        elif fast_val < slow_val:
            current_state = CrossoverState.BEARISH
        else:
            current_state = CrossoverState.EQUAL
        
        signal = None
        
        # Detect state transitions
        if self._prev_state != CrossoverState.UNKNOWN:
            # BUY: was bearish/equal, now bullish
            if (self._prev_state in (CrossoverState.BEARISH, CrossoverState.EQUAL) and
                current_state == CrossoverState.BULLISH):
                signal = CrossoverSignal(
                    symbol="",  # Will be set by caller
                    signal=SignalType.BUY,
                    timestamp=timestamp,
                    entry_price=price,
                    smma_fast=fast_val,
                    smma_slow=slow_val,
                )
                logger.info(
                    f"BUY crossover detected at {timestamp}: "
                    f"SMMA{self.fast_period}={fast_val:.2f} > "
                    f"SMMA{self.slow_period}={slow_val:.2f}"
                )
            
            # SELL: was bullish/equal, now bearish
            elif (self._prev_state in (CrossoverState.BULLISH, CrossoverState.EQUAL) and
                  current_state == CrossoverState.BEARISH):
                signal = CrossoverSignal(
                    symbol="",  # Will be set by caller
                    signal=SignalType.SELL,
                    timestamp=timestamp,
                    entry_price=price,
                    smma_fast=fast_val,
                    smma_slow=slow_val,
                )
                logger.info(
                    f"SELL crossover detected at {timestamp}: "
                    f"SMMA{self.fast_period}={fast_val:.2f} < "
                    f"SMMA{self.slow_period}={slow_val:.2f}"
                )
        
        self._prev_state = current_state
        
        if signal:
            self._signal_history.append(signal)
        
        return signal
    
    def load_history(self, prices: List[float]) -> None:
        """Initialize SMMA from historical prices without generating signals.
        
        Use this to warm up the SMMA calculators from historical data.
        """
        self.smma_fast.load_history(prices)
        self.smma_slow.load_history(prices)
        
        # Set initial state based on current SMMA values
        if self.smma_fast.is_ready and self.smma_slow.is_ready:
            fast = self.smma_fast.value
            slow = self.smma_slow.value
            if fast > slow:
                self._prev_state = CrossoverState.BULLISH
            elif fast < slow:
                self._prev_state = CrossoverState.BEARISH
            else:
                self._prev_state = CrossoverState.EQUAL
    
    @property
    def is_ready(self) -> bool:
        """Whether both SMMA calculators are initialized."""
        return self.smma_fast.is_ready and self.smma_slow.is_ready
    
    @property
    def current_state(self) -> CrossoverState:
        return self._prev_state
    
    @property
    def signal_count(self) -> int:
        return len(self._signal_history)


class CrossoverManager:
    """Manages crossover detectors for multiple symbols."""
    
    def __init__(self):
        self._detectors: Dict[str, CrossoverDetector] = {}
        self._on_signal: Optional[Callable[[str, CrossoverSignal], None]] = None
        self._lock = threading.Lock()
    
    def set_on_signal_callback(
        self, callback: Callable[[str, CrossoverSignal], None]
    ) -> None:
        """Register callback for crossover signals."""
        self._on_signal = callback
    
    def get_or_create_detector(self, symbol: str) -> CrossoverDetector:
        """Get or create a detector for a symbol."""
        with self._lock:
            if symbol not in self._detectors:
                self._detectors[symbol] = CrossoverDetector()
            return self._detectors[symbol]
    
    def update(self, symbol: str, price: float, timestamp: datetime) -> Optional[CrossoverSignal]:
        """Update a symbol's detector with a new price."""
        detector = self.get_or_create_detector(symbol)
        signal = detector.update(price, timestamp)
        
        if signal:
            signal.symbol = symbol
            if self._on_signal:
                try:
                    self._on_signal(symbol, signal)
                except Exception as e:
                    logger.error(f"Error in signal callback for {symbol}: {e}")
        
        return signal
    
    def get_detector(self, symbol: str) -> Optional[CrossoverDetector]:
        with self._lock:
            return self._detectors.get(symbol)
    
    def get_all_states(self) -> Dict[str, CrossoverState]:
        """Get crossover state for all symbols."""
        with self._lock:
            return {
                sym: det.current_state
                for sym, det in self._detectors.items()
                if det.is_ready
            }
