"""NSE instrument universe manager.

Handles loading, caching, and filtering of the NSE equity universe.
Applies the initial LTP filter to reduce the stock universe before
detailed processing.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import List, Dict, Set, Optional, Any

import pandas as pd

from config import settings
from data.models import MarketTick
from storage.database import DatabaseManager
from utils.logging_config import get_logger

logger = get_logger("data.instrument_manager")


class InstrumentManager:
    """Manages the NSE equity instrument universe.
    
    Responsibilities:
    - Load instruments from broker
    - Cache to database
    - Apply LTP filter to determine which stocks need Full Tick subscription
    - Track which stocks pass liquidity filter (qualified stocks)
    """
    
    def __init__(self, db: DatabaseManager):
        self._db = db
        self._all_instruments: Dict[str, Dict[str, Any]] = {}  # token -> instrument
        self._symbol_to_token: Dict[str, str] = {}  # symbol -> token
        self._token_to_symbol: Dict[str, str] = {}  # token -> symbol
        self._ltp_qualified: Set[str] = set()  # tokens passing LTP filter
        self._liquidity_qualified: Set[str] = set()  # tokens passing liquidity filter
        self._latest_ltp: Dict[str, float] = {}  # token -> latest LTP
        self._lock = threading.Lock()
    
    def load_instruments(self, instruments: List[Dict[str, Any]]) -> int:
        """Load instruments from broker into memory and database.
        
        Args:
            instruments: List of instrument dicts from broker.get_instruments()
            
        Returns:
            Number of instruments loaded.
        """
        with self._lock:
            self._all_instruments.clear()
            self._symbol_to_token.clear()
            self._token_to_symbol.clear()
            
            for inst in instruments:
                token = str(inst['token'])
                symbol = inst['symbol']
                self._all_instruments[token] = inst
                self._symbol_to_token[symbol] = token
                self._token_to_symbol[token] = symbol
                
                # Cache to database
                self._db.upsert_instrument({
                    'token': token,
                    'symbol': symbol,
                    'name': inst.get('name', ''),
                    'exchange': inst.get('exchange', 'NSE'),
                    'lot_size': inst.get('lot_size', 1),
                    'tick_size': inst.get('tick_size', 0.05),
                })
            
            logger.info(f"Loaded {len(self._all_instruments)} instruments")
            return len(self._all_instruments)
    
    def update_ltp(self, token: str, ltp: float) -> None:
        """Update the latest LTP for a token and re-evaluate LTP filter."""
        with self._lock:
            self._latest_ltp[token] = ltp
            
            if settings.LTP_MIN <= ltp <= settings.LTP_MAX:
                self._ltp_qualified.add(token)
            else:
                self._ltp_qualified.discard(token)
    
    def update_liquidity(self, token: str, bid_qty: int, ask_qty: int) -> None:
        """Update liquidity qualification for a token."""
        with self._lock:
            if bid_qty > settings.MIN_BID_QTY and ask_qty > settings.MIN_ASK_QTY:
                self._liquidity_qualified.add(token)
            else:
                self._liquidity_qualified.discard(token)
    
    def get_all_tokens(self) -> List[str]:
        """Get all instrument tokens."""
        with self._lock:
            return list(self._all_instruments.keys())
    
    def get_ltp_qualified_tokens(self) -> Set[str]:
        """Get tokens that pass the LTP filter."""
        with self._lock:
            return self._ltp_qualified.copy()
    
    def get_liquidity_qualified_tokens(self) -> Set[str]:
        """Get tokens that pass both LTP and liquidity filters."""
        with self._lock:
            return self._ltp_qualified & self._liquidity_qualified
    
    def get_symbol(self, token: str) -> str:
        """Get symbol for a token."""
        return self._token_to_symbol.get(token, token)
    
    def get_token(self, symbol: str) -> Optional[str]:
        """Get token for a symbol."""
        return self._symbol_to_token.get(symbol)
    
    def get_instrument(self, token: str) -> Optional[Dict[str, Any]]:
        """Get full instrument details."""
        return self._all_instruments.get(token)
    
    @property
    def total_count(self) -> int:
        return len(self._all_instruments)
    
    @property
    def ltp_qualified_count(self) -> int:
        return len(self._ltp_qualified)
    
    @property
    def liquidity_qualified_count(self) -> int:
        return len(self.get_liquidity_qualified_tokens())
