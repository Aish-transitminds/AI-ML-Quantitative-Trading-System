"""Unit tests for ML preprocessing."""
import pytest
import numpy as np
from ml.preprocessing import Preprocessor


class TestPreprocessor:
    def test_fit_transform(self):
        pp = Preprocessor()
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        X_scaled = pp.fit_transform(X)
        
        assert X_scaled.shape == X.shape
        assert pp.is_fitted
        # Scaled values should have mean ~0 and std ~1
        assert np.abs(X_scaled.mean(axis=0)).max() < 0.01
    
    def test_transform_without_fit(self):
        pp = Preprocessor()
        with pytest.raises(RuntimeError):
            pp.transform(np.array([[1, 2]]))
    
    def test_nan_handling(self):
        pp = Preprocessor()
        X = np.array([[1.0, np.nan], [3.0, 4.0], [5.0, 6.0]])
        X_scaled = pp.fit_transform(X)
        assert not np.any(np.isnan(X_scaled))
    
    def test_inf_handling(self):
        pp = Preprocessor()
        X = np.array([[1.0, np.inf], [3.0, 4.0], [5.0, 6.0]])
        X_scaled = pp.fit_transform(X)
        assert not np.any(np.isinf(X_scaled))
