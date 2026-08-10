"""Unit tests for order book features."""
import pytest
from data.models import MarketTick
from datetime import datetime
from features.orderbook_features import compute_orderbook_features


class TestOrderImbalance:
    def test_balanced(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST', token='T1',
            ltp=100.0, bid_price=99.9, bid_quantity=1000,
            ask_price=100.1, ask_quantity=1000
        )
        features = compute_orderbook_features(tick)
        assert features['order_imbalance'] == 0.0
    
    def test_buy_pressure(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST', token='T1',
            ltp=100.0, bid_price=99.9, bid_quantity=2000,
            ask_price=100.1, ask_quantity=1000
        )
        features = compute_orderbook_features(tick)
        # (2000 - 1000) / (2000 + 1000) = 1000/3000 = 0.333
        assert features['order_imbalance'] == pytest.approx(1/3)
    
    def test_sell_pressure(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST', token='T1',
            ltp=100.0, bid_price=99.9, bid_quantity=500,
            ask_price=100.1, ask_quantity=1500
        )
        features = compute_orderbook_features(tick)
        assert features['order_imbalance'] < 0
    
    def test_zero_quantities(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST', token='T1',
            ltp=100.0, bid_price=0, bid_quantity=0,
            ask_price=0, ask_quantity=0
        )
        features = compute_orderbook_features(tick)
        assert features['order_imbalance'] == 0.0  # safe_divide returns default


class TestSpread:
    def test_spread(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST', token='T1',
            ltp=100.0, bid_price=99.90, ask_price=100.10
        )
        features = compute_orderbook_features(tick)
        assert features['spread'] == pytest.approx(0.20)
        assert features['spread_pct'] == pytest.approx(0.002)
