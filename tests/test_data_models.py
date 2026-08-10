"""Unit tests for data models."""
import pytest
from datetime import datetime
from data.models import (
    MarketTick, Bar, Trade, FeatureVector,
    SignalType, TradeStatus, Decision,
    StockScreenResult
)


class TestMarketTick:
    def test_valid_tick(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST-EQ',
            token='123', ltp=100.0
        )
        assert tick.validate() is True
    
    def test_invalid_no_symbol(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='',
            token='123', ltp=100.0
        )
        assert tick.validate() is False
    
    def test_invalid_zero_ltp(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST',
            token='123', ltp=0.0
        )
        assert tick.validate() is False
    
    def test_invalid_negative_ltq(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST',
            token='123', ltp=100.0, ltq=-5
        )
        assert tick.validate() is False
    
    def test_to_dict(self):
        tick = MarketTick(
            timestamp=datetime.now(), symbol='TEST',
            token='123', ltp=100.0
        )
        d = tick.to_dict()
        assert 'symbol' in d
        assert 'ltp' in d
        assert isinstance(d['timestamp'], str)


class TestBar:
    def test_update_ohlc(self):
        bar = Bar(
            timestamp=datetime.now(), symbol='TEST',
            open=0, high=0, low=0, close=0
        )
        tick1 = MarketTick(
            timestamp=datetime.now(), symbol='TEST',
            token='1', ltp=100.0, ltq=10
        )
        bar.update(tick1)
        assert bar.open == 100.0
        assert bar.high == 100.0
        assert bar.low == 100.0
        
        tick2 = MarketTick(
            timestamp=datetime.now(), symbol='TEST',
            token='1', ltp=110.0, ltq=20
        )
        bar.update(tick2)
        assert bar.high == 110.0
        assert bar.low == 100.0
        assert bar.close == 110.0
        assert bar.ltq_sum == 30


class TestFeatureVector:
    def test_feature_names(self):
        names = FeatureVector.feature_names()
        assert 'ltq_current' in names
        assert 'smma20' in names
        assert 'order_imbalance' in names
    
    def test_to_dict(self):
        fv = FeatureVector(ltq_current=100, smma20=50.5)
        d = fv.to_dict()
        assert d['ltq_current'] == 100
        assert d['smma20'] == 50.5


class TestStockScreenResult:
    def test_ltp_filter(self):
        result = StockScreenResult(symbol='TEST', ltp=100.0)
        assert result.passes_ltp_filter is True
        
        result2 = StockScreenResult(symbol='TEST', ltp=10.0)
        assert result2.passes_ltp_filter is False
        
        result3 = StockScreenResult(symbol='TEST', ltp=600.0)
        assert result3.passes_ltp_filter is False
