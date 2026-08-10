"""ETQ (Exchange Traded Quantity) feature engineering.

ETQ is the sum of LTQ values over a rolling time window.
This is NOT the same as daily volume.

ETQ_5M = sum(LTQ for all ticks in previous 5 minutes)
ETQ_20M = sum(LTQ for all ticks in previous 20 minutes)
ETQ_60M = sum(LTQ for all ticks in previous 60 minutes)
"""
from __future__ import annotations
from typing import Dict

from data.tick_store import TickStore
from utils.logging_config import get_logger

logger = get_logger("features.etq")


def compute_etq_features(tick_store: TickStore, symbol: str) -> Dict[str, float]:
    """Compute ETQ features for a symbol."""
    return {
        'etq_5m': float(tick_store.calculate_etq(symbol, 5)),
        'etq_20m': float(tick_store.calculate_etq(symbol, 20)),
        'etq_60m': float(tick_store.calculate_etq(symbol, 60)),
    }
