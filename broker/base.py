"""Abstract base class for broker market data providers.

Defines the interface that all broker implementations must follow.
This abstraction allows the rest of the application to be broker-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional, Any
from data.models import MarketTick


class MarketDataProvider(ABC):
    """Abstract base class for market data providers.
    
    All broker implementations must subclass this and implement
    every abstract method. The rest of the application only interacts
    with this interface.
    
    Subscription modes (Angel One convention, adapted for abstraction):
        MODE_LTP = 1   # LTP only (lightweight)
        MODE_QUOTE = 2 # LTP + OHLC + volume
        MODE_FULL = 3  # Full tick: LTP, OHLC, volume, LTQ, depth
    """
    
    MODE_LTP = 1
    MODE_QUOTE = 2
    MODE_FULL = 3
    
    def __init__(self):
        self._on_tick_callback: Optional[Callable[[MarketTick], None]] = None
        self._on_connect_callback: Optional[Callable[[], None]] = None
        self._on_disconnect_callback: Optional[Callable[[str], None]] = None
        self._on_error_callback: Optional[Callable[[str], None]] = None
        self._connected: bool = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Authenticate and establish connection.
        
        Returns:
            True if connection was successful, False otherwise.
        """
        ...
    
    @abstractmethod
    def disconnect(self) -> None:
        """Cleanly close all connections and clean up resources."""
        ...
    
    @abstractmethod
    def get_instruments(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        """Fetch the instrument master list.
        
        Args:
            exchange: Exchange segment (default 'NSE').
            
        Returns:
            List of instrument dictionaries with at least:
            - token: str (broker instrument identifier)
            - symbol: str (trading symbol)
            - name: str (company name)
            - exchange: str
        """
        ...
    
    @abstractmethod
    def subscribe(self, tokens: List[str], mode: int = 3) -> None:
        """Subscribe to market data for given instrument tokens.
        
        Args:
            tokens: List of instrument token strings.
            mode: Subscription mode (1=LTP, 2=Quote, 3=Full with depth+LTQ).
        """
        ...
    
    @abstractmethod
    def unsubscribe(self, tokens: List[str], mode: int = 3) -> None:
        """Unsubscribe from market data."""
        ...
    
    @abstractmethod
    def get_historical_data(
        self,
        token: str,
        exchange: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict[str, Any]]:
        """Fetch historical candle data.
        
        Args:
            token: Instrument token.
            exchange: Exchange segment.
            interval: Candle interval (e.g., 'ONE_MINUTE').
            from_date: Start date string.
            to_date: End date string.
            
        Returns:
            List of candle dictionaries with: timestamp, open, high, low, close, volume.
        """
        ...
    
    @abstractmethod
    def start_websocket(self) -> None:
        """Start the WebSocket connection in a background thread."""
        ...
    
    @abstractmethod
    def stop_websocket(self) -> None:
        """Stop the WebSocket connection."""
        ...
    
    def set_on_tick_callback(self, callback: Callable[[MarketTick], None]) -> None:
        """Register callback for incoming normalized ticks."""
        self._on_tick_callback = callback
    
    def set_on_connect_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for successful connection."""
        self._on_connect_callback = callback
    
    def set_on_disconnect_callback(self, callback: Callable[[str], None]) -> None:
        """Register callback for disconnection events."""
        self._on_disconnect_callback = callback
    
    def set_on_error_callback(self, callback: Callable[[str], None]) -> None:
        """Register callback for error events."""
        self._on_error_callback = callback
    
    def is_connected(self) -> bool:
        """Return current connection status."""
        return self._connected
    
    @abstractmethod
    def get_max_subscriptions(self) -> int:
        """Return maximum tokens subscribable per session."""
        ...
    
    @abstractmethod
    def get_broker_name(self) -> str:
        """Return human-readable broker name."""
        ...
