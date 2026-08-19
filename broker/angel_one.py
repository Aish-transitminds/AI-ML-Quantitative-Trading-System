"""Angel One SmartAPI broker implementation.

Provides real-time market data via SmartWebSocketV2 and historical data
via the SmartConnect REST API.

WebSocket Modes:
    Mode 1 (LTP): Only LTP updates. Lightweight, good for initial screening.
    Mode 2 (Quote): LTP + OHLC + Volume.
    Mode 3 (Full): LTP + OHLC + Volume + LTQ + Best 5 Depth.

Subscription Limit: 1,000 tokens per session, up to 3 sessions.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional, Any

import pyotp
import requests

from broker.base import MarketDataProvider
from config import settings
from data.models import MarketTick

# Lazy imports to handle missing SDK gracefully
try:
    from SmartApi.smartConnect import SmartConnect
    from SmartApi.smartWebSocketV2 import SmartWebSocketV2
    SMARTAPI_AVAILABLE = True
except ImportError:
    SMARTAPI_AVAILABLE = False

from utils.logging_config import get_logger

logger = get_logger("broker.angel_one")

# Angel One instrument master URL
INSTRUMENT_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"


class AngelOneProvider(MarketDataProvider):
    """Angel One SmartAPI market data provider."""
    
    def __init__(self):
        super().__init__()
        self._smart_api: Optional[Any] = None  # SmartConnect instance
        self._websocket: Optional[Any] = None  # SmartWebSocketV2 instance
        self._auth_token: str = ""
        self._feed_token: str = ""
        self._ws_thread: Optional[threading.Thread] = None
        self._subscribed_tokens: Dict[int, set] = {1: set(), 2: set(), 3: set()}
        self._instruments_cache: List[Dict[str, Any]] = []
        self._token_to_symbol: Dict[str, str] = {}  # token -> symbol mapping
        
        # Auto-refresh state
        self._last_auth_date: Optional[datetime.date] = None
        self._auto_refresh_thread: Optional[threading.Thread] = None
        self._auto_refresh_running: bool = False
    
    def connect(self) -> bool:
        """Authenticate with Angel One SmartAPI."""
        if not SMARTAPI_AVAILABLE:
            logger.error("smartapi-python package not installed. Run: pip install smartapi-python")
            return False
        
        if not settings.API_KEY or not settings.CLIENT_ID:
            logger.error("Angel One credentials not configured. Set API_KEY and CLIENT_ID in .env")
            return False
        
        try:
            self._smart_api = SmartConnect(api_key=settings.API_KEY)
            
            # Generate TOTP
            totp = pyotp.TOTP(settings.TOTP_SECRET).now()
            
            # Generate session
            data = self._smart_api.generateSession(
                clientCode=settings.CLIENT_ID,
                password=settings.PASSWORD,
                totp=totp
            )
            
            if data.get('status', False) is False:
                msg = data.get('message', 'Unknown error')
                logger.error(f"Login failed: {msg}")
                if "totp" in msg.lower() or "invalid" in msg.lower():
                    logger.error("HINT: Ensure your TOTP_SECRET comes from the SmartAPI 'enable-totp' QR flow, NOT your Angel One login password.")
                return False
            
            self._auth_token = data['data']['jwtToken']
            self._feed_token = self._smart_api.getfeedToken()
            self._connected = True
            self._last_auth_date = datetime.now().date()
            
            # Start the daily auto-refresh thread if not running
            if not self._auto_refresh_running:
                self._auto_refresh_running = True
                self._auto_refresh_thread = threading.Thread(target=self._daily_refresh_loop, daemon=True)
                self._auto_refresh_thread.start()
            
            logger.info(f"Angel One login successful for client: {settings.CLIENT_ID[:4]}****")
            return True
            
        except Exception as e:
            logger.error(f"Angel One connection failed: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Angel One."""
        self._auto_refresh_running = False
        try:
            self.stop_websocket()
            if self._smart_api:
                try:
                    self._smart_api.terminateSession(settings.CLIENT_ID)
                except Exception:
                    pass
            self._connected = False
            logger.info("Angel One disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def _daily_refresh_loop(self) -> None:
        """Background thread that re-authenticates every day at midnight.
        
        The SmartAPI session silently expires at midnight. This thread
        detects the date change, gets a fresh session (auth token + feed token),
        and seamlessly restarts the WebSocket stream.
        """
        while self._auto_refresh_running:
            try:
                now_date = datetime.now().date()
                if self._last_auth_date and now_date > self._last_auth_date:
                    logger.info("New day detected. Automatically refreshing Angel One session to prevent silent expiry...")
                    # Generate new TOTP and Session
                    totp = pyotp.TOTP(settings.TOTP_SECRET).now()
                    data = self._smart_api.generateSession(
                        clientCode=settings.CLIENT_ID,
                        password=settings.PASSWORD,
                        totp=totp
                    )
                    
                    if data.get('status', False):
                        self._auth_token = data['data']['jwtToken']
                        self._feed_token = self._smart_api.getfeedToken()
                        self._last_auth_date = now_date
                        logger.info("Daily session refresh successful.")
                        
                        # If WebSocket is running, restart it with new tokens
                        if self._websocket:
                            logger.info("Restarting WebSocket with new session tokens...")
                            self.stop_websocket()
                            time.sleep(2)
                            self.start_websocket()
                            
                            # Give WS time to connect, then resubscribe
                            time.sleep(3)
                            for mode, tokens in self._subscribed_tokens.items():
                                if tokens:
                                    self.subscribe(list(tokens), mode)
                    else:
                        logger.error(f"Daily session refresh failed: {data.get('message')}")
            except Exception as e:
                logger.error(f"Error in daily refresh loop: {e}")
            
            # Check every hour
            time.sleep(3600)
    
    def get_instruments(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        """Fetch NSE equity instruments from Angel One instrument master.
        
        Downloads the full instrument master JSON and filters for NSE equities.
        Results are cached for the session.
        """
        if self._instruments_cache:
            return self._instruments_cache
        
        try:
            logger.info("Downloading Angel One instrument master...")
            response = requests.get(INSTRUMENT_MASTER_URL, timeout=30)
            response.raise_for_status()
            all_instruments = response.json()
            
            # Filter for NSE equities (exch_seg == 'nse_cm' or 'NSE' and symbol ends with '-EQ')
            nse_equities = []
            for inst in all_instruments:
                if (inst.get('exch_seg', '') in ('nse_cm', 'NSE') and 
                    inst.get('symbol', '').endswith('-EQ')):
                    normalized = {
                        'token': inst.get('token', ''),
                        'symbol': inst.get('symbol', ''),
                        'name': inst.get('name', ''),
                        'exchange': 'NSE',
                        'lot_size': int(inst.get('lotsize', 1)),
                        'tick_size': float(inst.get('tick_size', 0.05)),
                    }
                    nse_equities.append(normalized)
                    self._token_to_symbol[normalized['token']] = normalized['symbol']
            
            self._instruments_cache = nse_equities
            logger.info(f"Loaded {len(nse_equities)} NSE equity instruments")
            return nse_equities
            
        except requests.RequestException as e:
            logger.error(f"Failed to download instrument master: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing instrument master: {e}")
            return []
    
    def subscribe(self, tokens: List[str], mode: int = 3) -> None:
        """Subscribe to market data via WebSocket.
        
        Args:
            tokens: List of instrument token strings.
            mode: 1=LTP, 2=Quote, 3=Full (with depth + LTQ).
        """
        if not self._websocket:
            logger.warning("WebSocket not initialized. Call start_websocket() first.")
            return
        
        # Respect subscription limits
        total_subscribed = sum(len(s) for s in self._subscribed_tokens.values())
        if total_subscribed + len(tokens) > self.get_max_subscriptions():
            logger.warning(
                f"Subscription limit reached. Currently {total_subscribed}, "
                f"requesting {len(tokens)}, max {self.get_max_subscriptions()}"
            )
            # Truncate to fit
            available = self.get_max_subscriptions() - total_subscribed
            tokens = tokens[:available]
        
        if not tokens:
            return
        
        try:
            # Angel One expects: [{"exchangeType": 1, "tokens": ["token1", ...]}]
            # exchangeType: 1=NSE, 2=NFO, 3=BSE
            token_list = [{"exchangeType": 1, "tokens": tokens}]
            correlation_id = f"sub_{mode}_{int(time.time())}"
            
            self._websocket.subscribe(correlation_id, mode, token_list)
            self._subscribed_tokens[mode].update(tokens)
            
            logger.info(f"Subscribed {len(tokens)} tokens in mode {mode}")
            
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
    
    def unsubscribe(self, tokens: List[str], mode: int = 3) -> None:
        """Unsubscribe from market data."""
        if not self._websocket:
            return
        
        try:
            token_list = [{"exchangeType": 1, "tokens": tokens}]
            correlation_id = f"unsub_{mode}_{int(time.time())}"
            
            self._websocket.unsubscribe(correlation_id, mode, token_list)
            self._subscribed_tokens[mode].difference_update(tokens)
            
            logger.info(f"Unsubscribed {len(tokens)} tokens from mode {mode}")
            
        except Exception as e:
            logger.error(f"Unsubscribe failed: {e}")
    
    def get_historical_data(
        self,
        token: str,
        exchange: str = "NSE",
        interval: str = "ONE_MINUTE",
        from_date: str = "",
        to_date: str = "",
    ) -> List[Dict[str, Any]]:
        """Fetch historical candle data from Angel One.
        
        Args:
            token: Instrument token.
            exchange: Exchange segment.
            interval: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, etc.
            from_date: Format: 'YYYY-MM-DD HH:MM'
            to_date: Format: 'YYYY-MM-DD HH:MM'
        """
        if not self._smart_api:
            logger.error("Not connected to Angel One")
            return []
        
        try:
            params = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date,
            }
            
            response = self._smart_api.getCandleData(params)
            
            if response and response.get('status'):
                candles = response.get('data', [])
                result = []
                for candle in candles:
                    # Angel One candle format: [timestamp, open, high, low, close, volume]
                    result.append({
                        'timestamp': candle[0],
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': int(candle[5]),
                    })
                return result
            else:
                logger.warning(f"No historical data returned for token {token}")
                return []
                
        except Exception as e:
            logger.error(f"Historical data fetch failed for token {token}: {e}")
            return []
    
    def start_websocket(self) -> None:
        """Start the WebSocket connection in a background thread."""
        if not SMARTAPI_AVAILABLE:
            logger.error("smartapi-python not available")
            return
        
        if not self._auth_token:
            logger.error("Not authenticated. Call connect() first.")
            return
        
        try:
            self._websocket = SmartWebSocketV2(
                self._auth_token,
                settings.API_KEY,
                settings.CLIENT_ID,
                self._feed_token,
            )
            
            # Register callbacks
            self._websocket.on_open = self._on_ws_open
            self._websocket.on_data = self._on_ws_data
            self._websocket.on_error = self._on_ws_error
            self._websocket.on_close = self._on_ws_close
            
            # Start in background thread
            self._ws_thread = threading.Thread(
                target=self._websocket.connect,
                name="AngelOne-WebSocket",
                daemon=True,
            )
            self._ws_thread.start()
            
            logger.info("Angel One WebSocket started")
            
        except Exception as e:
            logger.error(f"WebSocket start failed: {e}")
    
    def stop_websocket(self) -> None:
        """Stop the WebSocket connection."""
        try:
            if self._websocket:
                self._websocket.close_connection()
                self._websocket = None
            if self._ws_thread and self._ws_thread.is_alive():
                self._ws_thread.join(timeout=5)
            logger.info("WebSocket stopped")
        except Exception as e:
            logger.error(f"Error stopping WebSocket: {e}")
    
    def get_max_subscriptions(self) -> int:
        """Angel One allows 1000 tokens per WebSocket session."""
        return 1000
    
    def get_broker_name(self) -> str:
        return "Angel One SmartAPI"
    
    # === Internal WebSocket Callbacks ===
    
    def _on_ws_open(self, wsapp) -> None:
        """Called when WebSocket connection opens."""
        logger.info("Angel One WebSocket connection opened")
        if self._on_connect_callback:
            self._on_connect_callback()
    
    def _on_ws_data(self, wsapp, message: Dict[str, Any]) -> None:
        """Called when market data tick is received.
        
        Normalizes Angel One tick format to internal MarketTick.
        
        Angel One Mode 3 fields:
            subscription_mode, exchange_type, token,
            last_traded_price, open_price, high_price, low_price, close_price,
            volume_trade_for_the_day, last_traded_quantity,
            total_buy_quantity, total_sell_quantity,
            best_5_data (list of bid/ask levels),
            exchange_feed_time, last_traded_timestamp
        """
        try:
            token = str(message.get('token', ''))
            symbol = self._token_to_symbol.get(token, token)
            
            # Parse exchange timestamp
            exchange_ts = message.get('exchange_feed_time') or message.get('exchange_timestamp')
            if exchange_ts:
                try:
                    ts = datetime.fromtimestamp(exchange_ts) if isinstance(exchange_ts, (int, float)) else datetime.now()
                except (ValueError, OSError):
                    ts = datetime.now()
            else:
                ts = datetime.now()
            
            # Angel One sends all prices in paisa, so divide by 100
            ltp = float(message.get('last_traded_price', 0)) / 100.0
            close = float(message.get('close_price', 0)) / 100.0
            open_price = float(message.get('open_price_of_the_day', message.get('open_price', 0))) / 100.0
            high_price = float(message.get('high_price_of_the_day', message.get('high_price', 0))) / 100.0
            low_price = float(message.get('low_price_of_the_day', message.get('low_price', 0))) / 100.0
            
            # Extract best bid/ask from best_5_data
            best_5 = message.get('best_5_data', [])
            bid_price = 0.0
            bid_qty = 0
            ask_price = 0.0
            ask_qty = 0
            
            if best_5 and len(best_5) >= 2:
                # best_5_data structure varies by SDK version
                # Typically: list of dicts with 'price', 'quantity' for buy and sell
                try:
                    if isinstance(best_5, list):
                        # Some versions: [{buy entries}, {sell entries}]
                        # Others: flat list alternating buy/sell
                        for entry in best_5:
                            if isinstance(entry, dict):
                                flag = entry.get('flag', entry.get('buySellFlag', 0))
                                if flag == 1:  # Buy side
                                    if bid_price == 0.0:
                                        bid_price = float(entry.get('price', entry.get('bestBuyPrice', 0))) / 100.0
                                        bid_qty = int(entry.get('quantity', entry.get('bestBuyQuantity', 0)))
                                elif flag == 0:  # Sell side
                                    if ask_price == 0.0:
                                        ask_price = float(entry.get('price', entry.get('bestSellPrice', 0))) / 100.0
                                        ask_qty = int(entry.get('quantity', entry.get('bestSellQuantity', 0)))
                except (KeyError, TypeError, ValueError) as e:
                    logger.debug(f"Error parsing best_5_data for {symbol}: {e}")
            
            tick = MarketTick(
                timestamp=ts,
                symbol=symbol,
                token=token,
                ltp=ltp,
                ltq=int(message.get('last_traded_quantity', 0)),
                volume=int(message.get('volume_trade_for_the_day', 0)),
                open_price=float(message.get('open_price_of_the_day', message.get('open_price', 0))) / 100.0,
                high_price=float(message.get('high_price_of_the_day', message.get('high_price', 0))) / 100.0,
                low_price=float(message.get('low_price_of_the_day', message.get('low_price', 0))) / 100.0,
                close_price=close,
                bid_price=bid_price,
                bid_quantity=bid_qty,
                ask_price=ask_price,
                ask_quantity=ask_qty,
                total_buy_quantity=int(message.get('total_buy_quantity', message.get('totalBuyQuantity', 0))),
                total_sell_quantity=int(message.get('total_sell_quantity', message.get('totalSellQuantity', 0))),
                best_5_data=best_5,
            )
            
            if tick.validate() and self._on_tick_callback:
                self._on_tick_callback(tick)
                
        except Exception as e:
            logger.error(f"Error processing tick data: {e}", exc_info=True)
    
    def _on_ws_error(self, wsapp, error: str) -> None:
        """Called on WebSocket error."""
        logger.error(f"Angel One WebSocket error: {error}")
        if self._on_error_callback:
            self._on_error_callback(str(error))
    
    def _on_ws_close(self, wsapp) -> None:
        """Called when WebSocket closes."""
        logger.warning("Angel One WebSocket connection closed")
        self._connected = False
        if self._on_disconnect_callback:
            self._on_disconnect_callback("WebSocket connection closed")
    
    def get_symbol_for_token(self, token: str) -> str:
        """Look up symbol name for a given token."""
        return self._token_to_symbol.get(token, token)
