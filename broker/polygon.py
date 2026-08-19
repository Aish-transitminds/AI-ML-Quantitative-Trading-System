"""Polygon.io (Massive API) market data provider implementation.

Fetches real-time and historical US equity data using Polygon.io API key.
"""
from __future__ import annotations

import os
import json
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests
import websocket
from broker.base import MarketDataProvider
from data.models import MarketTick
from utils.helpers import get_ist_now

logger = logging.getLogger(__name__)

# Map of NASDAQ/NYSE symbols for US stocks
US_SYMBOL_MAP = {
    "AAPL": {"token": "101", "name": "Apple Inc.", "exchange": "NASDAQ", "base_price": 180.0},
    "MSFT": {"token": "102", "name": "Microsoft Corporation", "exchange": "NASDAQ", "base_price": 400.0},
    "TSLA": {"token": "103", "name": "Tesla, Inc.", "exchange": "NASDAQ", "base_price": 200.0},
    "AMZN": {"token": "104", "name": "Amazon.com, Inc.", "exchange": "NASDAQ", "base_price": 175.0},
    "GOOGL": {"token": "105", "name": "Alphabet Inc.", "exchange": "NASDAQ", "base_price": 150.0},
    "NVDA": {"token": "106", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "base_price": 800.0},
    "AMD": {"token": "107", "name": "Advanced Micro Devices", "exchange": "NASDAQ", "base_price": 160.0},
    "META": {"token": "108", "name": "Meta Platforms", "exchange": "NASDAQ", "base_price": 450.0},
    "NFLX": {"token": "109", "name": "Netflix, Inc.", "exchange": "NASDAQ", "base_price": 600.0},
    "QQQ": {"token": "110", "name": "Invesco QQQ Trust", "exchange": "NASDAQ", "base_price": 430.0},
}

# Reverse map from token to symbol
TOKEN_TO_SYMBOL = {info["token"]: sym for sym, info in US_SYMBOL_MAP.items()}


class PolygonProvider(MarketDataProvider):
    """Polygon.io (Massive API) Market Data Provider."""

    def __init__(self):
        super().__init__()
        # Fallback to key provided by user
        self.api_key = os.getenv("POLYGON_API_KEY", "YsceFaL9yKPfZZqAYBbrEktMmiMIZ71D").strip()
        self._ws: Optional[websocket.WebSocketApp] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._subscribed_symbols: List[str] = []

    def connect(self) -> bool:
        """Authenticate and check connection validity."""
        url = f"https://api.polygon.io/v3/reference/tickers/AAPL?apiKey={self.api_key}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                self._connected = True
                logger.info("Successfully authenticated with Polygon.io (Massive API)")
                return True
            else:
                logger.error(f"Failed to authenticate with Polygon.io: Status {r.status_code}, {r.text}")
        except Exception as e:
            logger.error(f"Error connecting to Polygon.io: {e}")
        return False

    def disconnect(self) -> None:
        """Close connections and cleanup."""
        self.stop_websocket()
        self._connected = False

    def get_instruments(self, exchange: str = "US") -> List[Dict[str, Any]]:
        """Return the supported US stock list as instrument dicts."""
        instruments = []
        for symbol, info in US_SYMBOL_MAP.items():
            instruments.append({
                "token": info["token"],
                "symbol": symbol,
                "name": info["name"],
                "exchange": info["exchange"],
                "lot_size": 1,
                "tick_size": 0.01,
            })
        return instruments

    def subscribe(self, tokens: List[str], mode: int = 3) -> None:
        """Subscribe to real-time feeds on WebSocket."""
        symbols_to_sub = []
        for t in tokens:
            sym = TOKEN_TO_SYMBOL.get(t)
            if sym and sym not in self._subscribed_symbols:
                symbols_to_sub.append(sym)
                self._subscribed_symbols.append(sym)

        if symbols_to_sub and self._ws and self._ws.sock and self._ws.sock.connected:
            # Format: T.AAPL, T.MSFT for trades
            sub_params = [f"T.{sym}" for sym in symbols_to_sub]
            payload = {
                "action": "subscribe",
                "params": ",".join(sub_params)
            }
            try:
                self._ws.send(json.dumps(payload))
                logger.info(f"Subscribed to Polygon trades: {symbols_to_sub}")
            except Exception as e:
                logger.error(f"Error subscribing on Polygon WS: {e}")

    def unsubscribe(self, tokens: List[str], mode: int = 3) -> None:
        """Unsubscribe from feeds."""
        symbols_to_unsub = []
        for t in tokens:
            sym = TOKEN_TO_SYMBOL.get(t)
            if sym and sym in self._subscribed_symbols:
                symbols_to_unsub.append(sym)
                self._subscribed_symbols.remove(sym)

        if symbols_to_unsub and self._ws and self._ws.sock and self._ws.sock.connected:
            unsub_params = [f"T.{sym}" for sym in symbols_to_unsub]
            payload = {
                "action": "unsubscribe",
                "params": ",".join(unsub_params)
            }
            try:
                self._ws.send(json.dumps(payload))
                logger.info(f"Unsubscribed from Polygon trades: {symbols_to_unsub}")
            except Exception as e:
                logger.error(f"Error unsubscribing on Polygon WS: {e}")

    def get_historical_data(
        self,
        token: str,
        exchange: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict[str, Any]]:
        """Fetch 1-minute historical OHLCV aggregates from Polygon."""
        symbol = TOKEN_TO_SYMBOL.get(token, "AAPL")
        
        # Convert date format if needed
        # Expected from_date / to_date format: YYYY-MM-DD
        # Let's ensure format is clean
        start_date = from_date.split("T")[0] if "T" in from_date else from_date
        end_date = to_date.split("T")[0] if "T" in to_date else to_date
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start_date}/{end_date}?adjusted=true&sort=asc&limit=5000&apiKey={self.api_key}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                bars = []
                for res in results:
                    ts = datetime.fromtimestamp(res["t"] / 1000.0)
                    bars.append({
                        "timestamp": ts.isoformat(),
                        "open": float(res["o"]),
                        "high": float(res["h"]),
                        "low": float(res["l"]),
                        "close": float(res["c"]),
                        "volume": int(res["v"]),
                    })
                logger.info(f"Fetched {len(bars)} Polygon aggregates for {symbol}")
                return bars
            else:
                logger.error(f"Failed to get Polygon historical data: Status {r.status_code}, {r.text}")
        except Exception as e:
            logger.error(f"Error fetching Polygon historical data for {symbol}: {e}")
        return []

    def start_websocket(self) -> None:
        """Start background WebSocket stream thread."""
        if self._ws_thread and self._ws_thread.is_alive():
            return

        websocket.enableTrace(False)
        self._ws = websocket.WebSocketApp(
            "wss://socket.polygon.io/stocks",
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close
        )
        
        self._ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True)
        self._ws_thread.start()
        logger.info("Polygon WebSocket client started in background thread.")

    def stop_websocket(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
        self._subscribed_symbols.clear()

    def get_max_subscriptions(self) -> int:
        return 1000

    def get_broker_name(self) -> str:
        return "Polygon.io (Massive API)"

    def _on_ws_open(self, ws: websocket.WebSocketApp) -> None:
        """Authenticate as soon as connection is opened."""
        logger.info("Polygon WebSocket opened. Sending authentication...")
        payload = {
            "action": "auth",
            "params": self.api_key
        }
        ws.send(json.dumps(payload))

    def _on_ws_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle incoming streaming ticks."""
        try:
            data = json.loads(message)
            if not isinstance(data, list):
                data = [data]

            for event in data:
                ev_type = event.get("ev")
                
                # Check auth status
                if ev_type == "status":
                    status = event.get("status")
                    msg = event.get("message")
                    if status == "auth_success":
                        logger.info("Polygon WebSocket authenticated successfully!")
                        # Resubscribe to already subscribed symbols if reconnecting
                        if self._subscribed_symbols:
                            sub_params = [f"T.{sym}" for sym in self._subscribed_symbols]
                            ws.send(json.dumps({"action": "subscribe", "params": ",".join(sub_params)}))
                    elif status == "auth_failed":
                        logger.error(f"Polygon WebSocket authentication failed: {msg}")
                    continue

                # Handle trade event (T)
                if ev_type == "T":
                    sym = event.get("sym")
                    info = US_SYMBOL_MAP.get(sym)
                    if not info:
                        continue

                    # Create normalized MarketTick
                    tick = MarketTick(
                        timestamp=datetime.fromtimestamp(event.get("t", time.time() * 1000) / 1000.0),
                        symbol=sym,
                        token=info["token"],
                        ltp=float(event.get("p", 0.0)),
                        ltq=int(event.get("s", 0)),
                        volume=int(event.get("v", 0)),
                        open_price=0.0,
                        high_price=0.0,
                        low_price=0.0,
                        close_price=0.0,
                        bid_price=float(event.get("p", 0.0)) - 0.01,  # simulated spread as Polygon Trades do not have bid/ask
                        bid_quantity=1000,
                        ask_price=float(event.get("p", 0.0)) + 0.01,
                        ask_quantity=1000,
                        total_buy_quantity=3000,
                        total_sell_quantity=3000
                    )

                    if self._on_tick_callback:
                        self._on_tick_callback(tick)

        except Exception as e:
            logger.error(f"Error handling Polygon WS message: {e}")

    def _on_ws_error(self, ws: websocket.WebSocketApp, error: Any) -> None:
        logger.error(f"Polygon WebSocket error: {error}")
        if self._on_error_callback:
            self._on_error_callback(str(error))

    def _on_ws_close(self, ws: websocket.WebSocketApp, close_status_code: Any, close_msg: Any) -> None:
        logger.info(f"Polygon WebSocket closed: {close_status_code} - {close_msg}")
        if self._on_disconnect_callback:
            self._on_disconnect_callback(f"{close_status_code}: {close_msg}")
