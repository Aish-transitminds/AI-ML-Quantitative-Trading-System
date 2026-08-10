"""Order book feature engineering.

Features derived from market depth data:
    spread: ask_price - bid_price
    spread_pct: (ask - bid) / ltp
    order_imbalance: (bid_qty - ask_qty) / (bid_qty + ask_qty)
    
Positive imbalance = more buying pressure.
Negative imbalance = more selling pressure.
"""
from __future__ import annotations
from typing import Dict

from data.models import MarketTick
from utils.helpers import safe_divide
from utils.logging_config import get_logger

logger = get_logger("features.orderbook")


def compute_orderbook_features(tick: MarketTick) -> Dict[str, float]:
    """Compute order book features from a tick.
    
    Args:
        tick: Latest market tick with depth data.
        
    Returns:
        Dictionary of order book feature values.
    """
    spread = tick.ask_price - tick.bid_price
    spread_pct = safe_divide(spread, tick.ltp, 0.0)
    
    total_qty = tick.bid_quantity + tick.ask_quantity
    order_imbalance = safe_divide(
        tick.bid_quantity - tick.ask_quantity,
        total_qty,
        0.0
    )
    
    return {
        'bid_price': float(tick.bid_price),
        'bid_quantity': float(tick.bid_quantity),
        'ask_price': float(tick.ask_price),
        'ask_quantity': float(tick.ask_quantity),
        'spread': spread,
        'spread_pct': spread_pct,
        'order_imbalance': order_imbalance,
    }
