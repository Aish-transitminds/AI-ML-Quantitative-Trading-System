"""Price-based feature engineering.

Features:
    avg_ltp_20m: Mean LTP over 20 minutes
    avg_ltp_60m: Mean LTP over 60 minutes
    return_1m: Price return over 1 minute
    return_5m: Price return over 5 minutes
    return_15m: Price return over 15 minutes
"""
from __future__ import annotations
from typing import Dict

from data.tick_store import TickStore
from utils.logging_config import get_logger

logger = get_logger("features.price")


def compute_price_features(tick_store: TickStore, symbol: str) -> Dict[str, float]:
    """Compute price-based features."""
    return {
        'avg_ltp_20m': tick_store.calculate_avg_ltp(symbol, 20),
        'avg_ltp_60m': tick_store.calculate_avg_ltp(symbol, 60),
        'return_1m': tick_store.get_price_return(symbol, 1),
        'return_5m': tick_store.get_price_return(symbol, 5),
        'return_15m': tick_store.get_price_return(symbol, 15),
    }
