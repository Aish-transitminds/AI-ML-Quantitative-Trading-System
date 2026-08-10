"""LTQ (Last Traded Quantity) feature engineering.

LTQ represents the quantity of the most recent trade — NOT daily volume.
These features capture trading activity patterns that may predict
crossover profitability.

Features:
    ltq_current: Most recent LTQ value
    ltq_avg_2m: Mean LTQ over previous 2 minutes
    ltq_avg_5m: Mean LTQ over previous 5 minutes
    ltq_ratio_2m_5m: ltq_avg_2m / ltq_avg_5m (momentum)
    ltq_acceleration: (ltq_avg_2m - ltq_avg_5m) / ltq_avg_5m
    ltq_std_5m: Standard deviation of LTQ over 5 minutes
"""
from __future__ import annotations
from typing import Dict

from data.tick_store import TickStore
from utils.helpers import safe_divide
from utils.logging_config import get_logger

logger = get_logger("features.ltq")


def compute_ltq_features(tick_store: TickStore, symbol: str) -> Dict[str, float]:
    """Compute all LTQ features for a symbol.
    
    Args:
        tick_store: Tick storage with recent tick history.
        symbol: Trading symbol.
        
    Returns:
        Dictionary of LTQ feature values.
    """
    latest = tick_store.get_latest_tick(symbol)
    ltq_current = float(latest.ltq) if latest else 0.0
    
    stats_2m = tick_store.calculate_ltq_stats(symbol, 2)
    stats_5m = tick_store.calculate_ltq_stats(symbol, 5)
    
    ltq_avg_2m = stats_2m['avg']
    ltq_avg_5m = stats_5m['avg']
    
    return {
        'ltq_current': ltq_current,
        'ltq_avg_2m': ltq_avg_2m,
        'ltq_avg_5m': ltq_avg_5m,
        'ltq_ratio_2m_5m': safe_divide(ltq_avg_2m, ltq_avg_5m, 1.0),
        'ltq_acceleration': safe_divide(ltq_avg_2m - ltq_avg_5m, ltq_avg_5m, 0.0),
        'ltq_std_5m': stats_5m['std'],
    }
