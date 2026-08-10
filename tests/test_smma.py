"""Unit tests for SMMA calculator."""
import pytest
from indicators.smma import SMMACalculator, calculate_smma_series


class TestSMMACalculator:
    """Test SMMA calculation correctness."""
    
    def test_initialization_with_period(self):
        calc = SMMACalculator(20)
        assert calc.period == 20
        assert not calc.is_ready
        assert calc.value is None
    
    def test_invalid_period(self):
        with pytest.raises(ValueError):
            SMMACalculator(0)
        with pytest.raises(ValueError):
            SMMACalculator(-5)
    
    def test_warmup_remaining(self):
        calc = SMMACalculator(5)
        assert calc.warmup_remaining == 5
        calc.update(100)
        assert calc.warmup_remaining == 4
    
    def test_initial_smma_equals_sma(self):
        """First SMMA value should equal SMA of first N values."""
        calc = SMMACalculator(5)
        values = [10, 20, 30, 40, 50]
        results = []
        for v in values:
            r = calc.update(v)
            results.append(r)
        
        # First 4 should be None
        assert results[:4] == [None, None, None, None]
        # 5th should be SMA = (10+20+30+40+50)/5 = 30
        assert results[4] == 30.0
        assert calc.is_ready
    
    def test_smma_formula(self):
        """Test SMMA formula: SMMA_t = (SMMA_{t-1} * (N-1) + Price_t) / N"""
        calc = SMMACalculator(5)
        # Initialize with [10, 20, 30, 40, 50] -> SMA = 30
        for v in [10, 20, 30, 40, 50]:
            calc.update(v)
        
        assert calc.value == 30.0
        
        # Next value: 60
        # SMMA = (30 * 4 + 60) / 5 = (120 + 60) / 5 = 36.0
        result = calc.update(60)
        assert result == 36.0
        
        # Next: 70
        # SMMA = (36 * 4 + 70) / 5 = (144 + 70) / 5 = 42.8
        result = calc.update(70)
        assert result == pytest.approx(42.8)
    
    def test_smma_not_ema(self):
        """Verify SMMA produces different results from EMA."""
        # EMA uses 2/(N+1), SMMA uses 1/N
        # For period 10: EMA alpha = 2/11 = 0.1818, SMMA alpha = 1/10 = 0.1
        calc = SMMACalculator(10)
        prices = list(range(1, 21))  # 1 to 20
        
        for p in prices:
            calc.update(p)
        
        smma_val = calc.value
        
        # Calculate EMA manually
        alpha = 2 / 11
        ema = sum(prices[:10]) / 10  # Initial = SMA
        for p in prices[10:]:
            ema = alpha * p + (1 - alpha) * ema
        
        # They should differ
        assert smma_val != pytest.approx(ema, abs=0.01)
    
    def test_period_1(self):
        """Period 1 SMMA should equal the price itself."""
        calc = SMMACalculator(1)
        assert calc.update(100) == 100
        assert calc.update(200) == 200
    
    def test_constant_prices(self):
        """SMMA of constant prices should equal that price."""
        calc = SMMACalculator(20)
        for _ in range(50):
            calc.update(100.0)
        assert calc.value == pytest.approx(100.0)
    
    def test_load_history(self):
        calc = SMMACalculator(5)
        prices = [10, 20, 30, 40, 50, 60, 70]
        result = calc.load_history(prices)
        assert result is not None
        assert calc.is_ready
    
    def test_reset(self):
        calc = SMMACalculator(5)
        for v in [10, 20, 30, 40, 50]:
            calc.update(v)
        assert calc.is_ready
        
        calc.reset()
        assert not calc.is_ready
        assert calc.value is None


class TestSMMASeries:
    def test_series_length(self):
        prices = list(range(1, 11))
        result = calculate_smma_series(prices, 5)
        assert len(result) == 10
        assert result[:4] == [None, None, None, None]
        assert result[4] is not None
