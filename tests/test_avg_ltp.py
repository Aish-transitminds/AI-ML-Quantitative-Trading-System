"""Unit tests for average LTP calculation."""
import pytest
from datetime import datetime, timedelta
from data.models import MarketTick
from data.tick_store import TickStore


class TestAvgLTP:
    def _create_tick(self, symbol, ltp, ts):
        return MarketTick(
            timestamp=ts, symbol=symbol, token='T1',
            ltp=ltp, ltq=1
        )
    
    def test_avg_ltp_basic(self):
        store = TickStore()
        now = datetime.now()
        
        for i in range(10):
            tick = self._create_tick('TEST', 100.0 + i, now + timedelta(seconds=i*30))
            store.add_tick(tick)
        
        avg = store.calculate_avg_ltp('TEST', 20)
        expected = sum(100.0 + i for i in range(10)) / 10
        assert avg == pytest.approx(expected)
    
    def test_avg_ltp_empty(self):
        store = TickStore()
        assert store.calculate_avg_ltp('NONE', 20) == 0.0
    
    def test_avg_ltp_single_tick(self):
        store = TickStore()
        now = datetime.now()
        store.add_tick(self._create_tick('TEST', 55.0, now))
        assert store.calculate_avg_ltp('TEST', 20) == 55.0
