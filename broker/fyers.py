"""FYERS broker implementation stub.

This module provides the interface for FYERS integration.
The architecture is ready; implementation can be completed when
FYERS credentials are available.

FYERS API v3:
    - Data WebSocket: wss://api.fyers.in/socket/v2/data/
    - Modes: Lite (LTP), SymbolUpdate (OHLCV), DepthUpdate (Market Depth)
    - Symbol format: 'NSE:SYMBOL-EQ'
"""
from __future__ import annotations

from typing import List, Dict, Any

from broker.base import MarketDataProvider
from data.models import MarketTick
from utils.logging_config import get_logger

logger = get_logger("broker.fyers")


class FyersProvider(MarketDataProvider):
    """FYERS API v3 market data provider (stub).
    
    This implementation provides the complete interface.
    Full functionality will be added when FYERS credentials
    and testing access are available.
    """
    
    def connect(self) -> bool:
        logger.warning("FYERS provider is not yet fully implemented")
        logger.info("To implement: OAuth2 flow with fyers-apiv3 SDK")
        return False
    
    def disconnect(self) -> None:
        pass
    
    def get_instruments(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        logger.warning("FYERS get_instruments not implemented")
        return []
    
    def subscribe(self, tokens: List[str], mode: int = 3) -> None:
        logger.warning("FYERS subscribe not implemented")
    
    def unsubscribe(self, tokens: List[str], mode: int = 3) -> None:
        logger.warning("FYERS unsubscribe not implemented")
    
    def get_historical_data(
        self, token: str, exchange: str = "NSE",
        interval: str = "1", from_date: str = "", to_date: str = ""
    ) -> List[Dict[str, Any]]:
        logger.warning("FYERS get_historical_data not implemented")
        return []
    
    def start_websocket(self) -> None:
        logger.warning("FYERS WebSocket not implemented")
    
    def stop_websocket(self) -> None:
        pass
    
    def get_max_subscriptions(self) -> int:
        return 200  # FYERS default limit
    
    def get_broker_name(self) -> str:
        return "FYERS API v3"
