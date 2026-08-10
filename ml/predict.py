"""Live ML prediction for crossover signals.

Used at runtime when a new crossover is detected:
1. Compute feature vector
2. Preprocess using fitted scaler
3. Get probability from best model
4. Compare against threshold
5. Return ACCEPT or AVOID decision

Probability is NOT certainty. It represents the model's estimated
likelihood that the crossover will be profitable based on historical patterns.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List

import numpy as np

from config import settings
from data.models import Decision, FeatureVector
from ml.train import ModelTrainer
from utils.logging_config import get_logger

logger = get_logger("ml.predict")


class Predictor:
    """Live prediction engine for crossover signals."""
    
    def __init__(self, trainer: ModelTrainer):
        self._trainer = trainer
    
    def predict(
        self,
        features: Dict[str, float],
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Predict whether a crossover signal is likely profitable.
        
        Args:
            features: Feature dictionary at crossover time.
            threshold: Decision threshold (default: model's best or config).
            
        Returns:
            Dictionary with:
                probability: float (0-1)
                decision: Decision enum
                threshold_used: float
                model_name: str
        """
        if not self._trainer.best_model:
            return {
                'probability': None,
                'decision': Decision.INSUFFICIENT_DATA,
                'threshold_used': 0.0,
                'model_name': 'none',
                'reason': 'No trained model available',
            }
        
        try:
            # Build feature vector in correct order
            feature_names = self._trainer.feature_names
            X = np.array([[features.get(f, 0.0) for f in feature_names]])
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Preprocess
            X_scaled = self._trainer.preprocessor.transform(X)
            
            # Predict probability
            model = self._trainer.best_model
            if hasattr(model, 'predict_proba'):
                proba = float(model.predict_proba(X_scaled)[0, 1])
            else:
                proba = float(model.predict(X_scaled)[0])
            
            # Apply threshold
            thresh = threshold or self._trainer.best_threshold
            decision = Decision.ACCEPT if proba >= thresh else Decision.AVOID
            
            return {
                'probability': proba,
                'decision': decision,
                'threshold_used': thresh,
                'model_name': self._trainer.best_model_name,
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'probability': None,
                'decision': Decision.INSUFFICIENT_DATA,
                'threshold_used': 0.0,
                'model_name': 'error',
                'reason': str(e),
            }
    
    @property
    def is_ready(self) -> bool:
        """Whether the predictor has a trained model."""
        return self._trainer.best_model is not None
