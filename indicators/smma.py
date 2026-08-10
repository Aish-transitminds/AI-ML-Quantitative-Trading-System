"""Smoothed Moving Average (SMMA) calculator.

SMMA is also known as the Modified Moving Average (MMA) or 
Running Moving Average (RMA).

Formula:
    Initial SMMA = SMA of first N values
    SMMA_t = (SMMA_{t-1} * (N - 1) + Price_t) / N

This is NOT the same as EMA. EMA uses a different smoothing factor:
    EMA_t = Price_t * (2/(N+1)) + EMA_{t-1} * (1 - 2/(N+1))

SMMA uses:
    SMMA_t = Price_t * (1/N) + SMMA_{t-1} * ((N-1)/N)

For SMMA, the smoothing factor is 1/N.
For EMA, the smoothing factor is 2/(N+1).

These produce different results.
"""
from __future__ import annotations
from typing import List, Optional
from utils.logging_config import get_logger

logger = get_logger("indicators.smma")


class SMMACalculator:
    """Smoothed Moving Average calculator for a single period.
    
    Maintains running SMMA state and can be updated incrementally
    as new bars arrive.
    
    Args:
        period: Number of periods (e.g., 20 or 120).
    """
    
    def __init__(self, period: int):
        if period < 1:
            raise ValueError(f"SMMA period must be >= 1, got {period}")
        self.period = period
        self._values: List[float] = []  # Price history for initialization
        self._current_smma: Optional[float] = None
        self._initialized = False
    
    def update(self, price: float) -> Optional[float]:
        """Update SMMA with a new price value.
        
        Args:
            price: New closing price.
            
        Returns:
            Current SMMA value if initialized, None otherwise.
        """
        if not self._initialized:
            self._values.append(price)
            if len(self._values) == self.period:
                # Initial SMMA = SMA of first N values
                self._current_smma = sum(self._values) / self.period
                self._initialized = True
                return self._current_smma
            return None
        else:
            # SMMA_t = (SMMA_{t-1} * (N-1) + Price_t) / N
            self._current_smma = (
                (self._current_smma * (self.period - 1) + price) / self.period
            )
            return self._current_smma
    
    @property
    def value(self) -> Optional[float]:
        """Current SMMA value."""
        return self._current_smma
    
    @property
    def is_ready(self) -> bool:
        """Whether SMMA has been initialized with enough data."""
        return self._initialized
    
    @property
    def warmup_remaining(self) -> int:
        """Number of values still needed before SMMA initializes."""
        if self._initialized:
            return 0
        return self.period - len(self._values)
    
    def reset(self) -> None:
        """Reset calculator state."""
        self._values.clear()
        self._current_smma = None
        self._initialized = False
    
    def load_history(self, prices: List[float]) -> Optional[float]:
        """Initialize SMMA from historical prices.
        
        Args:
            prices: List of historical closing prices, oldest first.
            
        Returns:
            Final SMMA value after processing all prices.
        """
        self.reset()
        result = None
        for price in prices:
            result = self.update(price)
        return result


def calculate_smma_series(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculate SMMA for a series of prices.
    
    Args:
        prices: List of prices, oldest first.
        period: SMMA period.
        
    Returns:
        List of SMMA values (None for first period-1 values).
    """
    calc = SMMACalculator(period)
    return [calc.update(p) for p in prices]
