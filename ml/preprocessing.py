"""ML preprocessing — scaling, imputation, and class imbalance handling.

Pipeline:
    1. Handle missing values (impute with median)
    2. Scale features (StandardScaler)
    3. Handle class imbalance (class_weight='balanced' in models)
    
No oversampling is used to avoid temporal data leakage.
"""
from __future__ import annotations

from typing import Tuple, Optional, Dict, Any

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from utils.logging_config import get_logger

logger = get_logger("ml.preprocessing")


class Preprocessor:
    """Feature preprocessing pipeline."""
    
    def __init__(self):
        self._scaler = StandardScaler()
        self._imputer = SimpleImputer(strategy='median')
        self._fitted = False
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit on training data and transform."""
        X_clean = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        X_imputed = self._imputer.fit_transform(X_clean)
        X_scaled = self._scaler.fit_transform(X_imputed)
        self._fitted = True
        return X_scaled
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform new data using fitted parameters."""
        if not self._fitted:
            raise RuntimeError("Preprocessor must be fitted first")
        X_clean = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        X_imputed = self._imputer.transform(X_clean)
        X_scaled = self._scaler.transform(X_imputed)
        return X_scaled
    
    @property
    def is_fitted(self) -> bool:
        return self._fitted
    
    def get_params(self) -> Dict[str, Any]:
        """Get preprocessing parameters for serialization."""
        if not self._fitted:
            return {}
        return {
            'scaler_mean': self._scaler.mean_.tolist(),
            'scaler_scale': self._scaler.scale_.tolist(),
        }
