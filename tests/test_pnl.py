"""Unit tests for P&L calculation."""
import pytest
from datetime import datetime, timedelta
from data.models import Trade, SignalType, TradeStatus


class TestBuyPnL:
    """BUY P&L = exit_price - entry_price"""
    
    def test_profitable_buy(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.BUY,
            entry_timestamp=datetime.now(), entry_price=100.0,
            status=TradeStatus.OPEN
        )
        trade.close(datetime.now() + timedelta(hours=1), 110.0)
        
        assert trade.pnl == 10.0
        assert trade.profitable is True
        assert trade.status == TradeStatus.CLOSED
    
    def test_losing_buy(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.BUY,
            entry_timestamp=datetime.now(), entry_price=100.0,
        )
        trade.close(datetime.now(), 90.0)
        
        assert trade.pnl == -10.0
        assert trade.profitable is False
    
    def test_breakeven_buy(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.BUY,
            entry_timestamp=datetime.now(), entry_price=100.0,
        )
        trade.close(datetime.now(), 100.0)
        
        assert trade.pnl == 0.0
        assert trade.profitable is False  # 0 P&L is not profitable


class TestSellPnL:
    """SELL P&L = entry_price - exit_price"""
    
    def test_profitable_sell(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.SELL,
            entry_timestamp=datetime.now(), entry_price=100.0,
        )
        trade.close(datetime.now(), 90.0)
        
        assert trade.pnl == 10.0  # Sold at 100, covered at 90
        assert trade.profitable is True
    
    def test_losing_sell(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.SELL,
            entry_timestamp=datetime.now(), entry_price=100.0,
        )
        trade.close(datetime.now(), 110.0)
        
        assert trade.pnl == -10.0
        assert trade.profitable is False
    
    def test_breakeven_sell(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.SELL,
            entry_timestamp=datetime.now(), entry_price=100.0,
        )
        trade.close(datetime.now(), 100.0)
        
        assert trade.pnl == 0.0
        assert trade.profitable is False


class TestTradeLifecycle:
    def test_open_trade(self):
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.BUY,
            entry_timestamp=datetime.now(), entry_price=100.0,
        )
        assert trade.status == TradeStatus.OPEN
        assert trade.pnl is None
        assert trade.exit_price is None
    
    def test_close_sets_all_fields(self):
        now = datetime.now()
        exit_time = now + timedelta(hours=1)
        
        trade = Trade(
            symbol='TEST-EQ', signal=SignalType.BUY,
            entry_timestamp=now, entry_price=100.0,
        )
        trade.close(exit_time, 105.0)
        
        assert trade.exit_timestamp == exit_time
        assert trade.exit_price == 105.0
        assert trade.pnl == 5.0
        assert trade.status == TradeStatus.CLOSED
