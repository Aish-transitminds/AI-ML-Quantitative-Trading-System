"""Master feature engine — combines all feature modules.

Computes the complete feature vector for a symbol at a given point in time.
All features represent data available AT OR BEFORE the current moment.
No future data is ever included.

This is the single entry point for feature computation, used both by:
- Live prediction (at crossover time)
- Training data construction (from historical crossovers)
"""
from __future__ import annotations

from typing import Dict, Optional, List

from data.models import MarketTick, FeatureVector
from data.tick_store import TickStore
from features.ltq_features import compute_ltq_features
from features.etq_features import compute_etq_features
from features.orderbook_features import compute_orderbook_features
from features.price_features import compute_price_features
from features.smma_features import compute_smma_features
from utils.logging_config import get_logger

logger = get_logger("features.engine")


class FeatureEngine:
    """Computes complete feature vectors for ML prediction."""
    
    def __init__(self, tick_store: TickStore):
        self._tick_store = tick_store
    
    def compute_features(
        self,
        symbol: str,
        smma20: Optional[float] = None,
        smma120: Optional[float] = None,
        smma20_history: Optional[List[float]] = None,
        smma120_history: Optional[List[float]] = None,
    ) -> Dict[str, float]:
        """Compute all features for a symbol.
        
        ALL features use data available at or before the current moment.
        This function is used both for live prediction and training.
        
        Args:
            symbol: Trading symbol.
            smma20: Current SMMA(20) value.
            smma120: Current SMMA(120) value.
            smma20_history: Recent SMMA(20) values for slope.
            smma120_history: Recent SMMA(120) values for slope.
            
        Returns:
            Dictionary of all feature values.
        """
        features = {}
        
        # Get latest tick for orderbook features
        latest_tick = self._tick_store.get_latest_tick(symbol)
        ltp = latest_tick.ltp if latest_tick else 0.0
        
        # 1. LTQ features
        try:
            features.update(compute_ltq_features(self._tick_store, symbol))
        except Exception as e:
            logger.warning(f"LTQ features failed for {symbol}: {e}")
            features.update({k: 0.0 for k in FeatureVector.__dataclass_fields__ if k.startswith('ltq')})
        
        # 2. ETQ features
        try:
            features.update(compute_etq_features(self._tick_store, symbol))
        except Exception as e:
            logger.warning(f"ETQ features failed for {symbol}: {e}")
            features.update({'etq_5m': 0.0, 'etq_20m': 0.0, 'etq_60m': 0.0})
        
        # 3. Price features
        try:
            features.update(compute_price_features(self._tick_store, symbol))
        except Exception as e:
            logger.warning(f"Price features failed for {symbol}: {e}")
            features.update({'avg_ltp_20m': 0.0, 'avg_ltp_60m': 0.0, 'return_1m': 0.0, 'return_5m': 0.0, 'return_15m': 0.0})
        
        # 4. Orderbook features
        try:
            if latest_tick:
                features.update(compute_orderbook_features(latest_tick))
            else:
                features.update({
                    'bid_price': 0.0, 'bid_quantity': 0.0, 'ask_price': 0.0,
                    'ask_quantity': 0.0, 'spread': 0.0, 'spread_pct': 0.0,
                    'order_imbalance': 0.0,
                })
        except Exception as e:
            logger.warning(f"Orderbook features failed for {symbol}: {e}")
        
        # 5. SMMA features
        try:
            features.update(compute_smma_features(
                smma20, smma120, ltp, smma20_history, smma120_history
            ))
        except Exception as e:
            logger.warning(f"SMMA features failed for {symbol}: {e}")
            features.update({'smma20': 0.0, 'smma120': 0.0, 'smma_distance': 0.0, 'smma_slope_20': 0.0, 'smma_slope_120': 0.0})
        
        return features
    
    def compute_feature_vector(
        self,
        symbol: str,
        smma20: Optional[float] = None,
        smma120: Optional[float] = None,
        smma20_history: Optional[List[float]] = None,
        smma120_history: Optional[List[float]] = None,
    ) -> FeatureVector:
        """Compute a typed FeatureVector for ML input."""
        features = self.compute_features(
            symbol, smma20, smma120, smma20_history, smma120_history
        )
        
        fv = FeatureVector()
        for key, value in features.items():
            if hasattr(fv, key):
                setattr(fv, key, float(value))
        
        return fv
