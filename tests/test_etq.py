"""Unit tests for ETQ calculation."""
import pytest
from datetime import datetime, timedelta
from data.models import MarketTick
from data.tick_store import TickStore


class TestETQ:
    """ETQ = sum of LTQ over rolling window."""
    
    def _create_tick(self, symbol, ltp, ltq, ts):
        return MarketTick(
            timestamp=ts, symbol=symbol, token='T1',
            ltp=ltp, ltq=ltq
        )
    
    def test_etq_basic(self):
        store = TickStore()
        now = datetime.now()
        
        # Add 10 ticks, each with LTQ=100
        for i in range(10):
            tick = self._create_tick('TEST', 100.0, 100, now + timedelta(seconds=i*30))
            store.add_tick(tick)
        
        etq = store.calculate_etq('TEST', 5)
        assert etq == 1000  # 10 ticks * 100 LTQ
    
    def test_etq_empty(self):
        store = TickStore()
        assert store.calculate_etq('NONE', 5) == 0
    
    def test_etq_window_filtering(self):
        store = TickStore()
        now = datetime.now()
        
        # Old ticks (10 minutes ago)
        for i in range(5):
            tick = self._create_tick('TEST', 100.0, 200, now - timedelta(minutes=10) + timedelta(seconds=i))
            store.add_tick(tick)
        
        # Recent ticks (1 minute ago)
        for i in range(5):
            tick = self._create_tick('TEST', 100.0, 100, now - timedelta(minutes=1) + timedelta(seconds=i*10))
            store.add_tick(tick)
        
        etq_5m = store.calculate_etq('TEST', 5)
        etq_60m = store.calculate_etq('TEST', 60)
        
        assert etq_5m == 500  # Only recent 5 ticks
        assert etq_60m == 1500  # All 10 ticks
    
    def test_etq_is_not_volume(self):
        """ETQ uses LTQ (per-tick), not cumulative volume."""
        store = TickStore()
        now = datetime.now()
        
        # Volume increases but LTQ stays small
        for i in range(5):
            tick = MarketTick(
                timestamp=now + timedelta(seconds=i*30),
                symbol='TEST', token='T1',
                ltp=100.0, ltq=10,
                volume=10000 + i * 10  # Large cumulative volume
            )
            store.add_tick(tick)
        
        etq = store.calculate_etq('TEST', 5)
        assert etq == 50  # Sum of LTQ, NOT volume
