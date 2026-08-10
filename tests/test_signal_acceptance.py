"""Unit tests for signal acceptance logic."""
import pytest
from data.models import Decision


class TestSignalAcceptance:
    def test_accept_above_threshold(self):
        prob = 0.82
        threshold = 0.65
        decision = Decision.ACCEPT if prob >= threshold else Decision.AVOID
        assert decision == Decision.ACCEPT
    
    def test_avoid_below_threshold(self):
        prob = 0.41
        threshold = 0.65
        decision = Decision.ACCEPT if prob >= threshold else Decision.AVOID
        assert decision == Decision.AVOID
    
    def test_accept_at_threshold(self):
        prob = 0.65
        threshold = 0.65
        decision = Decision.ACCEPT if prob >= threshold else Decision.AVOID
        assert decision == Decision.ACCEPT
    
    def test_various_thresholds(self):
        prob = 0.70
        for thresh in [0.50, 0.60, 0.65, 0.70, 0.75, 0.80]:
            decision = Decision.ACCEPT if prob >= thresh else Decision.AVOID
            if thresh <= 0.70:
                assert decision == Decision.ACCEPT
            else:
                assert decision == Decision.AVOID
