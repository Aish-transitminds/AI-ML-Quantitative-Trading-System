"""ML model training pipeline.

Trains multiple models and selects the best based on validation performance.

Models:
    1. Logistic Regression (baseline — interpretable)
    2. Random Forest (ensemble — captures non-linear patterns)
    3. XGBoost (gradient boosting — typically best performance)

Model selection criteria:
    - Validation ROC-AUC (primary)
    - Stability across train/val metrics
    - Trading-specific performance (win rate, profit factor)
    
Class imbalance is handled via class_weight='balanced'.
No temporal oversampling to prevent leakage.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

from config import settings
from ml.preprocessing import Preprocessor
from ml.evaluate import evaluate_model, find_best_threshold
from storage.database import DatabaseManager
from utils.logging_config import get_logger

logger = get_logger("ml.train")

# Try importing XGBoost
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.info("XGBoost not available, using sklearn models only")


class ModelTrainer:
    """Trains and evaluates ML models for crossover prediction."""
    
    def __init__(self, db: DatabaseManager):
        self._db = db
        self.preprocessor = Preprocessor()
        self.models: Dict[str, Any] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.best_model_name: Optional[str] = None
        self.best_model: Optional[Any] = None
        self.best_threshold: float = settings.ML_THRESHOLD
        self.feature_names: List[str] = []
    
    def train_all(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """Train all models and evaluate.
        
        Returns:
            Dictionary of model_name -> evaluation results.
        """
        self.feature_names = feature_names
        
        # Preprocess
        X_train_scaled = self.preprocessor.fit_transform(X_train)
        X_val_scaled = self.preprocessor.transform(X_val)
        X_test_scaled = self.preprocessor.transform(X_test)
        
        # Check class distribution
        pos_ratio = np.mean(y_train)
        logger.info(f"Training class distribution: {pos_ratio:.2%} positive")
        
        # Define models
        model_configs = {
            'logistic_regression': LogisticRegression(
                class_weight='balanced',
                max_iter=1000,
                random_state=42,
                C=1.0,
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                class_weight='balanced',
                max_depth=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1,
            ),
        }
        
        if XGBOOST_AVAILABLE:
            # Calculate scale_pos_weight for imbalanced classes
            neg_count = np.sum(y_train == 0)
            pos_count = np.sum(y_train == 1)
            scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
            
            model_configs['xgboost'] = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False,
            )
        
        # Train and evaluate each model
        for name, model in model_configs.items():
            try:
                logger.info(f"Training {name}...")
                model.fit(X_train_scaled, y_train)
                self.models[name] = model
                
                # Evaluate on validation set
                val_results = evaluate_model(
                    model, X_val_scaled, y_val, feature_names, prefix="val"
                )
                
                # Find best threshold on validation set
                best_thresh = find_best_threshold(
                    model, X_val_scaled, y_val,
                    settings.THRESHOLD_CANDIDATES
                )
                val_results['best_threshold'] = best_thresh
                
                # Evaluate on test set (final, unseen)
                test_results = evaluate_model(
                    model, X_test_scaled, y_test, feature_names, prefix="test"
                )
                
                self.results[name] = {
                    'validation': val_results,
                    'test': test_results,
                    'best_threshold': best_thresh,
                }
                
                logger.info(
                    f"{name} — Val AUC: {val_results.get('roc_auc', 0):.4f}, "
                    f"Test AUC: {test_results.get('roc_auc', 0):.4f}, "
                    f"Best Threshold: {best_thresh:.2f}"
                )
                
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
                self.results[name] = {'error': str(e)}
        
        # Select best model based on validation AUC
        self._select_best_model()
        
        return self.results
    
    def _select_best_model(self) -> None:
        """Select the best model based on validation performance.
        
        Selection criteria:
        1. Validation ROC-AUC (primary)
        2. Stability: |val_auc - test_auc| < 0.15
        3. If tied, prefer simpler models
        """
        best_name = None
        best_auc = -1.0
        
        for name, result in self.results.items():
            if 'error' in result:
                continue
            
            val_auc = result.get('validation', {}).get('roc_auc', 0)
            test_auc = result.get('test', {}).get('roc_auc', 0)
            
            # Check stability
            stability = abs(val_auc - test_auc)
            if stability > 0.15:
                logger.warning(f"{name}: Large val/test gap ({stability:.3f}), may be overfit")
            
            if val_auc > best_auc:
                best_auc = val_auc
                best_name = name
        
        if best_name:
            self.best_model_name = best_name
            self.best_model = self.models[best_name]
            self.best_threshold = self.results[best_name].get('best_threshold', settings.ML_THRESHOLD)
            logger.info(f"Selected best model: {best_name} (Val AUC: {best_auc:.4f})")
        else:
            logger.warning("No valid model found")
    
    def save_models(self, directory: Optional[Path] = None) -> None:
        """Save all trained models to disk."""
        save_dir = directory or settings.MODELS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save preprocessor
        joblib.dump(self.preprocessor, save_dir / 'preprocessor.joblib')
        
        # Save models
        for name, model in self.models.items():
            joblib.dump(model, save_dir / f'{name}.joblib')
        
        # Save metadata
        metadata = {
            'best_model': self.best_model_name,
            'best_threshold': self.best_threshold,
            'feature_names': self.feature_names,
            'trained_at': datetime.now().isoformat(),
            'results': {}
        }
        for name, result in self.results.items():
            # Convert numpy types to Python types for JSON serialization
            clean_result = _clean_for_json(result)
            metadata['results'][name] = clean_result
        
        with open(save_dir / 'model_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Models saved to {save_dir}")
    
    def load_models(self, directory: Optional[Path] = None) -> bool:
        """Load trained models from disk."""
        load_dir = directory or settings.MODELS_DIR
        
        try:
            # Load preprocessor
            preprocessor_path = load_dir / 'preprocessor.joblib'
            if not preprocessor_path.exists():
                logger.warning("No saved preprocessor found")
                return False
            
            self.preprocessor = joblib.load(preprocessor_path)
            
            # Load metadata
            metadata_path = load_dir / 'model_metadata.json'
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                self.best_model_name = metadata.get('best_model')
                self.best_threshold = metadata.get('best_threshold', settings.ML_THRESHOLD)
                self.feature_names = metadata.get('feature_names', [])
                self.results = metadata.get('results', {})
            
            # Load models
            for model_file in load_dir.glob('*.joblib'):
                if model_file.name == 'preprocessor.joblib':
                    continue
                name = model_file.stem
                self.models[name] = joblib.load(model_file)
                logger.info(f"Loaded model: {name}")
            
            if self.best_model_name and self.best_model_name in self.models:
                self.best_model = self.models[self.best_model_name]
                logger.info(f"Best model: {self.best_model_name}")
                return True
            
            logger.warning("Best model not found in saved models")
            return False
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def persist_metrics(self) -> None:
        """Save model metrics to database."""
        for name, result in self.results.items():
            if 'error' in result:
                continue
            
            test = result.get('test', {})
            val = result.get('validation', {})
            
            self._db.insert_model_metrics(
                model_name=name,
                trained_at=datetime.now().isoformat(),
                dataset_size=0,  # Will be set properly
                train_size=0,
                test_size=0,
                accuracy=test.get('accuracy', 0),
                precision_score=test.get('precision', 0),
                recall=test.get('recall', 0),
                f1=test.get('f1', 0),
                roc_auc=test.get('roc_auc', 0),
                best_threshold=result.get('best_threshold', 0.5),
                feature_importance_json=json.dumps(
                    test.get('feature_importance', {}), default=str
                ),
            )


def _clean_for_json(obj: Any) -> Any:
    """Recursively convert numpy types to Python types."""
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_clean_for_json(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj
