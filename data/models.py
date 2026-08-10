"""Core data models for the stock screening system.

Defines normalized internal data structures that decouple the application
from broker-specific field names and formats.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class SignalType(Enum):
    """Type of crossover signal."""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(Enum):
    """Status of a crossover trade."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Decision(Enum):
    """ML-based signal decision."""
    ACCEPT = "ACCEPT"
    AVOID = "AVOID"
    PENDING = "PENDING"  # Not yet evaluated
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # ML model not trained


@dataclass
class MarketTick:
    """Normalized market tick data.
    
    This is the internal representation of a single market data update,
    independent of broker-specific field names.
    
    Attributes:
        timestamp: Exchange timestamp of the tick
        symbol: Trading symbol (e.g., 'SBIN-EQ')
        token: Broker-specific instrument token
        ltp: Last Traded Price
        ltq: Last Traded Quantity (quantity of the most recent trade)
        volume: Cumulative traded volume for the day (NOT rolling ETQ)
        open_price: Today's opening price
        high_price: Today's high price
        low_price: Today's low price
        close_price: Previous day's closing price
        bid_price: Best bid (buy) price — Level 1
        bid_quantity: Best bid quantity — Level 1
        ask_price: Best ask (sell) price — Level 1
        ask_quantity: Best ask quantity — Level 1
        total_buy_quantity: Total buy quantity across all levels
        total_sell_quantity: Total sell quantity across all levels
        best_5_data: Raw best-5 depth data (list of bid/ask levels)
    """
    timestamp: datetime
    symbol: str
    token: str
    ltp: float
    ltq: int = 0
    volume: int = 0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    bid_price: float = 0.0
    bid_quantity: int = 0
    ask_price: float = 0.0
    ask_quantity: int = 0
    total_buy_quantity: int = 0
    total_sell_quantity: int = 0
    best_5_data: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        if self.best_5_data:
            d['best_5_data'] = json.dumps(self.best_5_data)
        return d

    def validate(self) -> bool:
        """Basic validation of tick data."""
        if not self.symbol or not self.token:
            return False
        if self.ltp <= 0:
            return False
        if self.ltq < 0 or self.volume < 0:
            return False
        return True


@dataclass
class Bar:
    """OHLCV bar (candlestick) aggregated from ticks.
    
    Used as input for SMMA calculation.
    
    Attributes:
        timestamp: Bar open timestamp (start of the minute)
        symbol: Trading symbol
        open: Opening price
        high: Highest price
        low: Lowest price  
        close: Closing price
        volume: Total volume during bar
        ltq_sum: Sum of all LTQ values during bar (for ETQ calculation)
        tick_count: Number of ticks in this bar
        is_complete: Whether the bar's time period has ended
    """
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    ltq_sum: int = 0
    tick_count: int = 0
    is_complete: bool = False

    def update(self, tick: MarketTick) -> None:
        """Update bar with a new tick."""
        if self.tick_count == 0:
            self.open = tick.ltp
            self.high = tick.ltp
            self.low = tick.ltp
        else:
            self.high = max(self.high, tick.ltp)
            self.low = min(self.low, tick.ltp)
        self.close = tick.ltp
        self.volume += tick.ltq  # Increment by LTQ, not cumulative volume
        self.ltq_sum += tick.ltq
        self.tick_count += 1


@dataclass
class CrossoverSignal:
    """Represents a detected SMMA crossover event.
    
    Attributes:
        symbol: Trading symbol
        signal: BUY or SELL
        timestamp: When the crossover occurred
        entry_price: LTP at the time of crossover
        smma_fast: SMMA(20) value at crossover
        smma_slow: SMMA(120) value at crossover
        features: Dict of all feature values at the time of crossover
        ml_probability: ML model's predicted probability of profitability
        decision: ACCEPT or AVOID based on ML + filters
        reasons: List of human-readable explanation strings
        risk_factors: List of risk warnings
    """
    symbol: str
    signal: SignalType
    timestamp: datetime
    entry_price: float
    smma_fast: float
    smma_slow: float
    features: Dict[str, float] = field(default_factory=dict)
    ml_probability: Optional[float] = None
    decision: Decision = Decision.PENDING
    reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'symbol': self.symbol,
            'signal': self.signal.value,
            'timestamp': self.timestamp.isoformat(),
            'entry_price': self.entry_price,
            'smma_fast': self.smma_fast,
            'smma_slow': self.smma_slow,
            'features': json.dumps(self.features),
            'ml_probability': self.ml_probability,
            'decision': self.decision.value,
            'reasons': json.dumps(self.reasons),
            'risk_factors': json.dumps(self.risk_factors),
        }


@dataclass
class Trade:
    """Represents a complete or open trade triggered by a crossover.
    
    BUY trade: Entry on bullish crossover, exit on bearish crossover.
        P&L = exit_price - entry_price
    
    SELL trade: Entry on bearish crossover, exit on bullish crossover.
        P&L = entry_price - exit_price  (short trade)
    
    Attributes:
        id: Database ID
        symbol: Trading symbol
        signal: BUY or SELL
        entry_timestamp: When the trade was entered
        entry_price: LTP at entry
        exit_timestamp: When the trade was exited (None if open)
        exit_price: LTP at exit (None if open)
        pnl: Profit/Loss (None if open)
        profitable: Whether the trade is profitable (None if open)
        status: OPEN or CLOSED
        smma_fast_at_entry: SMMA(20) at entry
        smma_slow_at_entry: SMMA(120) at entry
        ml_probability: ML prediction at entry
        ml_decision: ACCEPT/AVOID at entry
        features_at_entry: All feature values at entry time
    """
    id: Optional[int] = None
    symbol: str = ""
    signal: SignalType = SignalType.BUY
    entry_timestamp: Optional[datetime] = None
    entry_price: float = 0.0
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    profitable: Optional[bool] = None
    status: TradeStatus = TradeStatus.OPEN
    smma_fast_at_entry: float = 0.0
    smma_slow_at_entry: float = 0.0
    ml_probability: Optional[float] = None
    ml_decision: Optional[str] = None
    features_at_entry: Dict[str, float] = field(default_factory=dict)

    def close(self, exit_timestamp: datetime, exit_price: float) -> None:
        """Close the trade and calculate P&L.
        
        BUY P&L = exit_price - entry_price (long: buy low, sell high)
        SELL P&L = entry_price - exit_price (short: sell high, buy low)
        """
        self.exit_timestamp = exit_timestamp
        self.exit_price = exit_price
        self.status = TradeStatus.CLOSED
        
        if self.signal == SignalType.BUY:
            self.pnl = exit_price - self.entry_price
        else:  # SELL
            self.pnl = self.entry_price - exit_price
        
        self.profitable = self.pnl > 0


@dataclass
class StockScreenResult:
    """Result of screening a single stock — displayed in the dashboard."""
    symbol: str
    exchange: str = "NSE"
    token: str = ""
    ltp: float = 0.0
    bid_price: float = 0.0
    bid_quantity: int = 0
    ask_price: float = 0.0
    ask_quantity: int = 0
    smma_fast: Optional[float] = None
    smma_slow: Optional[float] = None
    smma_difference: Optional[float] = None
    etq_5m: Optional[int] = None
    etq_20m: Optional[int] = None
    etq_60m: Optional[int] = None
    avg_ltp_20m: Optional[float] = None
    avg_ltp_60m: Optional[float] = None
    signal: Optional[str] = None  # "BUY", "SELL", or None
    ml_probability: Optional[float] = None
    decision: Optional[str] = None  # "ACCEPT", "AVOID", or None
    last_update: Optional[datetime] = None

    @property
    def passes_ltp_filter(self) -> bool:
        """Check if stock passes LTP range filter."""
        from config.settings import LTP_MIN, LTP_MAX
        return LTP_MIN <= self.ltp <= LTP_MAX

    @property
    def passes_liquidity_filter(self) -> bool:
        """Check if stock passes liquidity filter."""
        from config.settings import MIN_BID_QTY, MIN_ASK_QTY
        return self.bid_quantity > MIN_BID_QTY and self.ask_quantity > MIN_ASK_QTY


@dataclass
class FeatureVector:
    """Complete feature vector for ML prediction at crossover time.
    
    ALL features represent information available AT OR BEFORE the crossover.
    No future data is included — this prevents data leakage.
    """
    # LTQ features
    ltq_current: float = 0.0
    ltq_avg_2m: float = 0.0
    ltq_avg_5m: float = 0.0
    ltq_ratio_2m_5m: float = 0.0
    ltq_acceleration: float = 0.0
    ltq_std_5m: float = 0.0
    
    # ETQ features
    etq_5m: float = 0.0
    etq_20m: float = 0.0
    etq_60m: float = 0.0
    
    # Price features
    avg_ltp_20m: float = 0.0
    avg_ltp_60m: float = 0.0
    return_1m: float = 0.0
    return_5m: float = 0.0
    return_15m: float = 0.0
    
    # Orderbook features
    bid_price: float = 0.0
    bid_quantity: float = 0.0
    ask_price: float = 0.0
    ask_quantity: float = 0.0
    spread: float = 0.0
    spread_pct: float = 0.0
    order_imbalance: float = 0.0
    
    # SMMA features
    smma20: float = 0.0
    smma120: float = 0.0
    smma_distance: float = 0.0
    smma_slope_20: float = 0.0
    smma_slope_120: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return asdict(self)

    def to_list(self) -> List[float]:
        """Convert to ordered list of values for ML input."""
        return list(asdict(self).values())

    @staticmethod
    def feature_names() -> List[str]:
        """Return ordered list of feature names."""
        return list(FeatureVector().__dataclass_fields__.keys())
