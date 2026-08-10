"""Model evaluation — metrics, threshold analysis, trading performance.

Evaluates models on both ML metrics and trading-specific metrics.

ML Metrics:
    Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix
    
Trading Metrics:
    Win Rate, Number of Signals, Average P&L, Total P&L,
    Profit Factor, Maximum Drawdown
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)

from utils.logging_config import get_logger
from utils.helpers import safe_divide

logger = get_logger("ml.evaluate")


def evaluate_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    prefix: str = "",
) -> Dict[str, Any]:
    """Evaluate a trained model on a dataset.
    
    Args:
        model: Trained sklearn-compatible model.
        X: Feature matrix.
        y: True labels.
        feature_names: List of feature names.
        prefix: Prefix for metric names.
        
    Returns:
        Dictionary of evaluation metrics.
    """
    if len(X) == 0:
        return {'error': 'Empty dataset'}
    
    y_pred = model.predict(X)
    
    results = {
        'accuracy': float(accuracy_score(y, y_pred)),
        'precision': float(precision_score(y, y_pred, zero_division=0)),
        'recall': float(recall_score(y, y_pred, zero_division=0)),
        'f1': float(f1_score(y, y_pred, zero_division=0)),
    }
    
    # ROC-AUC (needs probability scores)
    try:
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X)[:, 1]
            results['roc_auc'] = float(roc_auc_score(y, y_proba))
            results['probabilities'] = y_proba.tolist()
        elif hasattr(model, 'decision_function'):
            y_scores = model.decision_function(X)
            results['roc_auc'] = float(roc_auc_score(y, y_scores))
        else:
            results['roc_auc'] = 0.0
    except Exception as e:
        logger.warning(f"ROC-AUC calculation failed: {e}")
        results['roc_auc'] = 0.0
    
    # Confusion matrix
    cm = confusion_matrix(y, y_pred)
    results['confusion_matrix'] = cm.tolist()
    
    # Feature importance
    results['feature_importance'] = get_feature_importance(model, feature_names)
    
    return results


def find_best_threshold(
    model: Any,
    X_val: np.ndarray,
    y_val: np.ndarray,
    candidates: List[float],
) -> float:
    """Find the optimal probability threshold on validation data.
    
    Evaluates each candidate threshold and selects the one that
    maximizes F1 score. The threshold is NEVER optimized on the test set.
    
    Args:
        model: Trained model with predict_proba.
        X_val: Validation features.
        y_val: Validation labels.
        candidates: List of threshold values to evaluate.
        
    Returns:
        Best threshold value.
    """
    if not hasattr(model, 'predict_proba'):
        return 0.5
    
    try:
        y_proba = model.predict_proba(X_val)[:, 1]
    except Exception:
        return 0.5
    
    best_threshold = 0.5
    best_f1 = -1.0
    
    for thresh in candidates:
        y_pred = (y_proba >= thresh).astype(int)
        
        # Need at least some predictions in each class
        if len(np.unique(y_pred)) < 2:
            continue
        
        f1 = f1_score(y_val, y_pred, zero_division=0)
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
    
    logger.info(f"Best threshold: {best_threshold} (F1={best_f1:.4f})")
    return best_threshold


def get_feature_importance(
    model: Any,
    feature_names: List[str],
) -> Dict[str, float]:
    """Extract feature importance from a trained model.
    
    For tree models: uses feature_importances_
    For linear models: uses absolute coefficient values
    """
    importance = {}
    
    try:
        if hasattr(model, 'feature_importances_'):
            # Tree-based models
            importances = model.feature_importances_
            for name, imp in zip(feature_names, importances):
                importance[name] = float(imp)
        elif hasattr(model, 'coef_'):
            # Linear models
            coefs = np.abs(model.coef_[0]) if model.coef_.ndim > 1 else np.abs(model.coef_)
            for name, coef in zip(feature_names, coefs):
                importance[name] = float(coef)
    except Exception as e:
        logger.warning(f"Could not extract feature importance: {e}")
    
    # Sort by importance
    return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


def evaluate_threshold_range(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    thresholds: List[float],
) -> List[Dict[str, Any]]:
    """Evaluate multiple thresholds for threshold analysis display."""
    if not hasattr(model, 'predict_proba'):
        return []
    
    try:
        y_proba = model.predict_proba(X)[:, 1]
    except Exception:
        return []
    
    results = []
    for thresh in thresholds:
        y_pred = (y_proba >= thresh).astype(int)
        
        n_accepted = int(np.sum(y_pred == 1))
        n_rejected = int(np.sum(y_pred == 0))
        
        # Among accepted signals, how many were actually profitable?
        accepted_mask = y_pred == 1
        if n_accepted > 0:
            accepted_win_rate = float(np.mean(y[accepted_mask]))
        else:
            accepted_win_rate = 0.0
        
        results.append({
            'threshold': thresh,
            'accepted': n_accepted,
            'rejected': n_rejected,
            'accuracy': float(accuracy_score(y, y_pred)) if len(np.unique(y_pred)) > 0 else 0,
            'precision': float(precision_score(y, y_pred, zero_division=0)),
            'recall': float(recall_score(y, y_pred, zero_division=0)),
            'f1': float(f1_score(y, y_pred, zero_division=0)),
            'accepted_win_rate': accepted_win_rate,
        })
    
    return results
