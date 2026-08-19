"""Broker factory for creating the appropriate market data provider.

Selects the broker implementation based on configuration.
"""
from __future__ import annotations

from broker.base import MarketDataProvider
from broker.angel_one import AngelOneProvider
from broker.fyers import FyersProvider
from broker.polygon import PolygonProvider
from config import settings
from utils.logging_config import get_logger

logger = get_logger("broker.factory")


def create_broker() -> MarketDataProvider:
    """Create and return the configured broker provider.
    
    Reads BROKER from settings and instantiates the appropriate
    MarketDataProvider implementation.
    
    Returns:
        MarketDataProvider instance.
        
    Raises:
        ValueError: If the configured broker is not supported.
    """
    broker_name = settings.BROKER.lower().strip()
    
    if broker_name in ('angel_one', 'angelone', 'angel'):
        logger.info("Creating Angel One SmartAPI provider")
        return AngelOneProvider()
    elif broker_name in ('fyers', 'fyers_v3'):
        logger.info("Creating FYERS provider")
        return FyersProvider()
    elif broker_name in ('polygon', 'massive'):
        logger.info("Creating Polygon.io (Massive API) provider")
        return PolygonProvider()
    else:
        raise ValueError(
            f"Unsupported broker: '{broker_name}'. "
            f"Supported: 'angel_one', 'fyers', 'polygon'"
        )
