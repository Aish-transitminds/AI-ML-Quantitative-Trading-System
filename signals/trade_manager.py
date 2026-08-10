"""Trade manager — tracks open/closed trades triggered by crossovers.

Manages the full lifecycle:
    1. Open trade on crossover signal
    2. Record all features at entry (for ML training)
    3. Close trade on opposite crossover
    4. Calculate P&L
    5. Persist to database

P&L Calculation:
    BUY trade:  P&L = exit_price - entry_price  (long: buy low, sell high)
    SELL trade: P&L = entry_price - exit_price  (short: sell high, buy low)
    
    Positive P&L = profitable trade.
    Negative P&L = losing trade.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable

from config import settings
from data.models import (
    CrossoverSignal, Trade, SignalType, TradeStatus, Decision
)
from storage.database import DatabaseManager
from utils.logging_config import get_logger

logger = get_logger("signals.trade_manager")


class TradeManager:
    """Manages crossover trades — open, close, P&L tracking."""
    
    def __init__(self, db: DatabaseManager):
        self._db = db
        self._open_trades: Dict[str, Trade] = {}  # symbol -> open Trade
        self._lock = threading.Lock()
        self._on_trade_closed: Optional[Callable[[Trade], None]] = None
        
        # Load existing open trades from DB
        self._load_open_trades()
    
    def _load_open_trades(self) -> None:
        """Load open trades from database on startup."""
        try:
            open_trades = self._db.get_open_trades()
            for trade in open_trades:
                self._open_trades[trade.symbol] = trade
            if open_trades:
                logger.info(f"Loaded {len(open_trades)} open trades from database")
        except Exception as e:
            logger.error(f"Error loading open trades: {e}")
    
    def set_on_trade_closed(self, callback: Callable[[Trade], None]) -> None:
        self._on_trade_closed = callback
    
    def on_crossover_signal(
        self,
        symbol: str,
        signal: CrossoverSignal,
    ) -> Optional[Trade]:
        """Process a crossover signal.
        
        - If no open trade exists: open a new trade
        - If open trade exists with OPPOSITE signal: close existing, open new
        - If open trade exists with SAME signal: should not happen (crossover
          state machine prevents this), but handle gracefully
        
        Args:
            symbol: Trading symbol.
            signal: The crossover signal.
            
        Returns:
            The closed Trade if one was closed, else None.
        """
        with self._lock:
            closed_trade = None
            existing = self._open_trades.get(symbol)
            
            if existing:
                if existing.signal != signal.signal:
                    # Close existing trade with opposite crossover
                    existing.close(
                        exit_timestamp=signal.timestamp,
                        exit_price=signal.entry_price,
                    )
                    
                    # Persist to DB
                    self._db.update_trade(
                        trade_id=existing.id,
                        exit_timestamp=signal.timestamp.isoformat(),
                        exit_price=signal.entry_price,
                        pnl=existing.pnl,
                        profitable=1 if existing.profitable else 0,
                        status=TradeStatus.CLOSED.value,
                    )
                    
                    logger.info(
                        f"Closed {existing.signal.value} trade for {symbol}: "
                        f"Entry={existing.entry_price:.2f}, "
                        f"Exit={signal.entry_price:.2f}, "
                        f"P&L={existing.pnl:.2f}, "
                        f"{'PROFIT' if existing.profitable else 'LOSS'}"
                    )
                    
                    closed_trade = existing
                    del self._open_trades[symbol]
                    
                    if self._on_trade_closed:
                        try:
                            self._on_trade_closed(closed_trade)
                        except Exception as e:
                            logger.error(f"Error in trade closed callback: {e}")
                else:
                    # Same signal type — should not happen with proper crossover detection
                    logger.warning(
                        f"Duplicate {signal.signal.value} signal for {symbol}, ignoring"
                    )
                    return None
            
            # Open new trade
            new_trade = Trade(
                symbol=symbol,
                signal=signal.signal,
                entry_timestamp=signal.timestamp,
                entry_price=signal.entry_price,
                smma_fast_at_entry=signal.smma_fast,
                smma_slow_at_entry=signal.smma_slow,
                ml_probability=signal.ml_probability,
                ml_decision=signal.decision.value if signal.decision else None,
                features_at_entry=signal.features,
                status=TradeStatus.OPEN,
            )
            
            # Insert to DB
            trade_id = self._db.insert_trade(
                symbol=symbol,
                signal=signal.signal.value,
                entry_timestamp=signal.timestamp.isoformat(),
                entry_price=signal.entry_price,
                smma20_at_entry=signal.smma_fast,
                smma120_at_entry=signal.smma_slow,
                ml_probability=signal.ml_probability,
                ml_decision=signal.decision.value if signal.decision else None,
                features_json=json.dumps(signal.features),
            )
            new_trade.id = trade_id
            self._open_trades[symbol] = new_trade
            
            logger.info(
                f"Opened {signal.signal.value} trade for {symbol} at "
                f"{signal.entry_price:.2f} (ML prob: {signal.ml_probability})"
            )
            
            return closed_trade
    
    def get_open_trades(self) -> Dict[str, Trade]:
        """Get all currently open trades."""
        with self._lock:
            return dict(self._open_trades)
    
    def get_open_trade(self, symbol: str) -> Optional[Trade]:
        """Get open trade for a specific symbol."""
        with self._lock:
            return self._open_trades.get(symbol)
    
    def get_closed_trades(self) -> List[Trade]:
        """Get all closed trades from database."""
        return self._db.get_closed_trades()
    
    def get_all_trades(self) -> List[Trade]:
        """Get all trades from database."""
        return self._db.get_all_trades()
    
    def get_trade_stats(self) -> Dict[str, any]:
        """Calculate aggregate trade statistics."""
        all_trades = self._db.get_all_trades()
        closed = [t for t in all_trades if t.status == TradeStatus.CLOSED]
        
        if not closed:
            return {
                'total': len(all_trades),
                'open': len(all_trades) - len(closed),
                'closed': 0,
                'profitable': 0,
                'losing': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'max_pnl': 0.0,
                'min_pnl': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'buy_signals': 0,
                'sell_signals': 0,
            }
        
        profitable = [t for t in closed if t.profitable]
        losing = [t for t in closed if not t.profitable]
        pnls = [t.pnl for t in closed if t.pnl is not None]
        
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        
        # Calculate max drawdown
        cumulative = []
        running = 0.0
        for p in pnls:
            running += p
            cumulative.append(running)
        
        peak = 0.0
        max_dd = 0.0
        for c in cumulative:
            if c > peak:
                peak = c
            dd = peak - c
            if dd > max_dd:
                max_dd = dd
        
        buy_signals = len([t for t in closed if t.signal == SignalType.BUY])
        sell_signals = len([t for t in closed if t.signal == SignalType.SELL])
        
        return {
            'total': len(all_trades),
            'open': len(all_trades) - len(closed),
            'closed': len(closed),
            'profitable': len(profitable),
            'losing': len(losing),
            'win_rate': len(profitable) / len(closed) if closed else 0.0,
            'total_pnl': sum(pnls),
            'avg_pnl': sum(pnls) / len(pnls) if pnls else 0.0,
            'max_pnl': max(pnls) if pnls else 0.0,
            'min_pnl': min(pnls) if pnls else 0.0,
            'profit_factor': gross_profit / gross_loss if gross_loss > 0 else float('inf'),
            'max_drawdown': max_dd,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
        }
