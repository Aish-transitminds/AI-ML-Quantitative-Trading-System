"""Unit tests for the master feature engine."""
import pytest
from datetime import datetime, timedelta
from data.models import MarketTick, FeatureVector
from data.tick_store import TickStore
from features.feature_engine import FeatureEngine


class TestFeatureEngine:
    def _populate_store(self, store: TickStore, symbol: str, n: int = 100):
        now = datetime.now()
        for i in range(n):
            tick = MarketTick(
                timestamp=now + timedelta(seconds=i*5),
                symbol=symbol, token='T1',
                ltp=100.0 + (i % 10) * 0.5,
                ltq=max(1, 50 + i),
                bid_price=99.5 + (i % 10) * 0.5,
                bid_quantity=1500000,
                ask_price=100.5 + (i % 10) * 0.5,
                ask_quantity=1200000,
            )
            store.add_tick(tick)
    
    def test_compute_all_features(self):
        store = TickStore()
        self._populate_store(store, 'TEST')
        
        engine = FeatureEngine(store)
        features = engine.compute_features(
            'TEST', smma20=100.5, smma120=99.8
        )
        
        assert 'ltq_current' in features
        assert 'etq_5m' in features
        assert 'order_imbalance' in features
        assert 'smma_distance' in features
        assert 'avg_ltp_20m' in features
    
    def test_feature_vector_type(self):
        store = TickStore()
        self._populate_store(store, 'TEST')
        
        engine = FeatureEngine(store)
        fv = engine.compute_feature_vector('TEST', smma20=100.5, smma120=99.8)
        
        assert isinstance(fv, FeatureVector)
        assert fv.smma20 == 100.5
    
    def test_empty_symbol(self):
        store = TickStore()
        engine = FeatureEngine(store)
        features = engine.compute_features('EMPTY')
        
        # Should return features with safe defaults, not crash
        assert isinstance(features, dict)
