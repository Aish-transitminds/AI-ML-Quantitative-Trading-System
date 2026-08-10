"""
Utility functions for the AI Stock Predictor.
"""

from datetime import datetime, time
import math
from typing import Union
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

def safe_divide(a: Union[int, float], b: Union[int, float], default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default value if division by zero occurs."""
    try:
        return float(a) / float(b) if b != 0 else default
    except (TypeError, ValueError, ZeroDivisionError):
        return default

def get_ist_now() -> datetime:
    """Get the current datetime in IST timezone."""
    ist_zone = zoneinfo.ZoneInfo("Asia/Kolkata")
    return datetime.now(ist_zone)

def timestamp_now() -> str:
    """Get the current IST datetime as an ISO format string."""
    return get_ist_now().isoformat()

def parse_timestamp(ts: Union[str, int, float, datetime]) -> datetime:
    """Parse various timestamp formats into a datetime object."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts)
    if isinstance(ts, str):
        # Handle basic isoformat
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            pass
        # Try custom formats if needed
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                continue
    raise ValueError(f"Could not parse timestamp: {ts}")

def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp a value between a minimum and maximum."""
    return max(min_val, min(value, max_val))

def round_price(price: float, tick_size: float = 0.05) -> float:
    """Round a price to the nearest tick size."""
    if tick_size <= 0:
        return price
    return round(math.floor((price / tick_size) + 0.5) * tick_size, 2)

def format_quantity(qty: Union[int, float]) -> str:
    """Format large numbers for Indian locale (e.g., Lakhs, Crores)."""
    if qty >= 10_000_000:
        return f"{qty / 10_000_000:.2f}Cr"
    elif qty >= 100_000:
        return f"{qty / 100_000:.2f}L"
    elif qty >= 1_000:
        return f"{qty / 1_000:.2f}K"
    return str(qty)

def format_currency(amount: float) -> str:
    """Format an amount in INR."""
    s, *d = str(round(amount, 2)).partition(".")
    r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]]) if len(s) > 3 else s
    return f"₹{r}{d[0]}{d[1].ljust(2, '0')}"

def is_market_hours() -> bool:
    """
    Check if the current time is within NSE trading hours.
    (9:15 AM - 3:30 PM IST, Monday - Friday)
    """
    now = get_ist_now()
    
    # Check if weekend (5 = Saturday, 6 = Sunday)
    if now.weekday() >= 5:
        return False
        
    market_open = time(9, 15)
    market_close = time(15, 30)
    current_time = now.time()
    
    return market_open <= current_time <= market_close
