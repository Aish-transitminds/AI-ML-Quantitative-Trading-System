"""Yahoo Finance data service for real Indian market data.

Fetches real historical and current market data from Yahoo Finance
for NSE-listed stocks. No API key required.

Usage:
    service = YahooFinanceService()
    bars = service.get_intraday_bars("SBIN")      # 1-min bars, last 5 days
    daily = service.get_daily_bars("SBIN", "6mo")  # daily bars, 6 months
    quote = service.get_quote("SBIN")              # current snapshot
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Map of clean display names to Yahoo Finance ticker symbols
NSE_SYMBOL_MAP: Dict[str, Dict[str, Any]] = {
    "SBIN": {"yahoo": "SBIN.NS", "name": "State Bank of India", "base_price": 250.0, "token": "3045"},
    "TATAMOTORS": {"yahoo": "TATAMOTORS.NS", "name": "Tata Motors", "base_price": 400.0, "token": "3456"},
    "PNB": {"yahoo": "PNB.NS", "name": "Punjab National Bank", "base_price": 65.0, "token": "2730"},
    "BANKBARODA": {"yahoo": "BANKBARODA.NS", "name": "Bank of Baroda", "base_price": 120.0, "token": "4668"},
    "SAIL": {"yahoo": "SAIL.NS", "name": "Steel Authority of India", "base_price": 85.0, "token": "2963"},
    "COALINDIA": {"yahoo": "COALINDIA.NS", "name": "Coal India", "base_price": 235.0, "token": "20374"},
    "NHPC": {"yahoo": "NHPC.NS", "name": "NHPC", "base_price": 48.0, "token": "14077"},
    "IRFC": {"yahoo": "IRFC.NS", "name": "IRFC", "base_price": 75.0, "token": "26424"},
    "IOC": {"yahoo": "IOC.NS", "name": "Indian Oil Corp", "base_price": 95.0, "token": "1624"},
    "BHEL": {"yahoo": "BHEL.NS", "name": "Bharat Heavy Electricals", "base_price": 155.0, "token": "438"},
}


class YahooFinanceService:
    """Fetches real market data from Yahoo Finance for NSE stocks."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._yf = None
        try:
            import yfinance as yf
            self._yf = yf
            logger.info("Yahoo Finance service initialized successfully.")
        except ImportError:
            logger.warning("yfinance not installed. Real market data unavailable.")

    @property
    def available(self) -> bool:
        return self._yf is not None

    def _get_yahoo_symbol(self, symbol: str) -> str:
        """Convert a clean symbol like 'SBIN' to 'SBIN.NS'."""
        info = NSE_SYMBOL_MAP.get(symbol)
        if info:
            return info["yahoo"]
        # Fallback: just append .NS
        clean = symbol.replace("-EQ", "").replace("DEMO_", "")
        return f"{clean}.NS"

    def get_intraday_bars(self, symbol: str, period: str = "5d", interval: str = "1m") -> List[Dict]:
        """Fetch intraday 1-minute bars for chart display.
        
        Args:
            symbol: Clean symbol (e.g. 'SBIN')
            period: How far back ('5d' = 5 days, max for 1m interval)
            interval: Bar interval ('1m', '5m', '15m', etc.)
            
        Returns:
            List of bar dicts with timestamp, open, high, low, close, volume
        """
        if not self.available:
            return []

        cache_key = f"intraday_{symbol}_{period}_{interval}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        yahoo_sym = self._get_yahoo_symbol(symbol)
        try:
            ticker = self._yf.Ticker(yahoo_sym)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No intraday data for {yahoo_sym}")
                return []

            bars = []
            for idx, row in df.iterrows():
                bars.append({
                    "timestamp": idx.isoformat(),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })

            self._cache[cache_key] = bars
            logger.info(f"Fetched {len(bars)} intraday bars for {yahoo_sym}")
            return bars

        except Exception as e:
            logger.error(f"Failed to fetch intraday data for {yahoo_sym}: {e}")
            return []

    def get_daily_bars(self, symbol: str, period: str = "6mo") -> List[Dict]:
        """Fetch daily OHLCV bars for ML training.
        
        Args:
            symbol: Clean symbol (e.g. 'SBIN')
            period: How far back ('6mo', '1y', '2y', etc.)
            
        Returns:
            List of daily bar dicts
        """
        if not self.available:
            return []

        cache_key = f"daily_{symbol}_{period}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        yahoo_sym = self._get_yahoo_symbol(symbol)
        try:
            ticker = self._yf.Ticker(yahoo_sym)
            df = ticker.history(period=period, interval="1d")

            if df.empty:
                logger.warning(f"No daily data for {yahoo_sym}")
                return []

            bars = []
            for idx, row in df.iterrows():
                bars.append({
                    "timestamp": idx.isoformat(),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })

            self._cache[cache_key] = bars
            logger.info(f"Fetched {len(bars)} daily bars for {yahoo_sym}")
            return bars

        except Exception as e:
            logger.error(f"Failed to fetch daily data for {yahoo_sym}: {e}")
            return []

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get current quote snapshot for a symbol.
        
        Returns dict with: ltp, bid, ask, volume, day_high, day_low, prev_close
        """
        if not self.available:
            return None

        cache_key = f"quote_{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        yahoo_sym = self._get_yahoo_symbol(symbol)
        try:
            ticker = self._yf.Ticker(yahoo_sym)
            info = ticker.fast_info

            quote = {
                "ltp": round(float(info.last_price), 2) if hasattr(info, 'last_price') and info.last_price else None,
                "prev_close": round(float(info.previous_close), 2) if hasattr(info, 'previous_close') and info.previous_close else None,
                "day_high": round(float(info.day_high), 2) if hasattr(info, 'day_high') and info.day_high else None,
                "day_low": round(float(info.day_low), 2) if hasattr(info, 'day_low') and info.day_low else None,
                "volume": int(info.last_volume) if hasattr(info, 'last_volume') and info.last_volume else 0,
                "market_cap": float(info.market_cap) if hasattr(info, 'market_cap') and info.market_cap else 0,
            }

            # Fallback: if last_price is None, use latest close from history
            if not quote["ltp"]:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    quote["ltp"] = round(float(hist["Close"].iloc[-1]), 2)

            self._cache[cache_key] = quote
            return quote

        except Exception as e:
            logger.error(f"Failed to get quote for {yahoo_sym}: {e}")
            return None

    def get_instruments_list(self) -> List[Dict]:
        """Return the instrument list in the format expected by the app."""
        instruments = []
        for symbol, info in NSE_SYMBOL_MAP.items():
            instruments.append({
                "symbol": symbol,
                "token": info["token"],
                "name": info["name"],
                "exchange": "NSE",
                "base_price": info["base_price"],
            })
        return instruments

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
"""Yahoo Finance data service module."""
