"""ML dataset construction from historical crossover trades.

Builds feature matrices (X) and labels (y) from closed trades.

Target variable:
    profitable = 1 if trade was profitable, 0 otherwise
    
    BUY: profitable if exit_price > entry_price
    SELL: profitable if exit_price < entry_price (short trade)

DATA LEAKAGE PREVENTION:
    - ALL features come from features_at_entry (recorded at crossover time)
    - NO future information (exit price, future SMMA, future returns) is used as features
    - Future exit price and P&L are used ONLY as labels
    
CHRONOLOGICAL SPLIT:
    - Data is sorted by entry_timestamp
    - Train: earliest 60%
    - Validation: next 20%
    - Test: latest 20%
    - NO random shuffling for the primary evaluation
"""
from __future__ import annotations

import json
from typing import Tuple, Dict, List, Optional, Any

import numpy as np
import pandas as pd

from config import settings
from data.models import Trade, TradeStatus, FeatureVector
from storage.database import DatabaseManager
from utils.logging_config import get_logger

logger = get_logger("ml.dataset")


class DatasetBuilder:
    """Builds ML training/validation/test datasets from closed trades."""
    
    def __init__(self, db: DatabaseManager):
        self._db = db
    
    def build_dataset(self) -> Optional[Dict[str, Any]]:
        """Build the complete dataset from closed trades.
        
        Returns:
            Dictionary with keys:
                X_train, y_train, X_val, y_val, X_test, y_test,
                feature_names, class_distribution, split_info
            Or None if insufficient data.
        """
        trades = self._db.get_closed_trades()
        
        if len(trades) < settings.MIN_TRADES_FOR_TRAINING:
            logger.warning(
                f"Insufficient closed trades for training: {len(trades)} "
                f"(need {settings.MIN_TRADES_FOR_TRAINING})"
            )
            return None
        
        # Sort chronologically
        trades.sort(key=lambda t: t.entry_timestamp or '')
        
        # Build feature matrix and labels
        feature_names = FeatureVector.feature_names()
        X_rows = []
        y_labels = []
        valid_trades = []
        
        for trade in trades:
            if trade.profitable is None:
                continue
            
            features = trade.features_at_entry
            if not features:
                continue
            
            # Extract features in consistent order
            row = []
            for fname in feature_names:
                val = features.get(fname, 0.0)
                try:
                    row.append(float(val))
                except (ValueError, TypeError):
                    row.append(0.0)
            
            X_rows.append(row)
            y_labels.append(1 if trade.profitable else 0)
            valid_trades.append(trade)
        
        if len(X_rows) < settings.MIN_TRADES_FOR_TRAINING:
            logger.warning(f"Only {len(X_rows)} valid trades with features")
            return None
        
        X = np.array(X_rows, dtype=np.float64)
        y = np.array(y_labels, dtype=np.int32)
        
        # Replace NaN/Inf with 0
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Chronological split
        n = len(X)
        train_end = int(n * settings.TRAIN_RATIO)
        val_end = int(n * (settings.TRAIN_RATIO + settings.VALIDATION_RATIO))
        
        X_train, y_train = X[:train_end], y[:train_end]
        X_val, y_val = X[train_end:val_end], y[train_end:val_end]
        X_test, y_test = X[val_end:], y[val_end:]
        
        # Class distribution
        total_positive = int(np.sum(y))
        total_negative = len(y) - total_positive
        
        logger.info(
            f"Dataset built: {n} samples, "
            f"Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}, "
            f"Positive={total_positive}, Negative={total_negative}"
        )
        
        return {
            'X_train': X_train,
            'y_train': y_train,
            'X_val': X_val,
            'y_val': y_val,
            'X_test': X_test,
            'y_test': y_test,
            'feature_names': feature_names,
            'class_distribution': {
                'total': n,
                'positive': total_positive,
                'negative': total_negative,
                'positive_ratio': total_positive / n,
            },
            'split_info': {
                'train_size': len(X_train),
                'val_size': len(X_val),
                'test_size': len(X_test),
                'method': 'chronological',
            },
            'trades': valid_trades,
        }
