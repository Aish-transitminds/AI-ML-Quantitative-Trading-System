"""Unit tests for LTQ features."""
import pytest
from datetime import datetime, timedelta
from data.models import MarketTick
from data.tick_store import TickStore
from features.ltq_features import compute_ltq_features


class TestLTQFeatures:
    def _create_tick(self, symbol, ltp, ltq, ts):
        return MarketTick(
            timestamp=ts, symbol=symbol, token='T1',
            ltp=ltp, ltq=ltq
        )
    
    def test_basic_features(self):
        store = TickStore()
        now = datetime.now()
        
        for i in range(30):
            tick = self._create_tick('TEST', 100.0, 50 + i, now + timedelta(seconds=i*10))
            store.add_tick(tick)
        
        features = compute_ltq_features(store, 'TEST')
        assert 'ltq_current' in features
        assert 'ltq_avg_2m' in features
        assert 'ltq_avg_5m' in features
        assert 'ltq_ratio_2m_5m' in features
        assert 'ltq_acceleration' in features
    
    def test_empty_data(self):
        store = TickStore()
        features = compute_ltq_features(store, 'EMPTY')
        assert features['ltq_current'] == 0.0
        assert features['ltq_ratio_2m_5m'] == 1.0  # safe_divide default
