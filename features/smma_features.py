"""SMMA-derived features for ML model.

Features:
    smma20: Current SMMA(20) value
    smma120: Current SMMA(120) value
    smma_distance: (SMMA20 - SMMA120) / LTP — normalized separation
    smma_slope_20: Rate of change of SMMA(20) over last 3 bars
    smma_slope_120: Rate of change of SMMA(120) over last 3 bars
"""
from __future__ import annotations
from typing import Dict, List, Optional

from utils.helpers import safe_divide
from utils.logging_config import get_logger

logger = get_logger("features.smma")


def compute_smma_features(
    smma20: Optional[float],
    smma120: Optional[float],
    ltp: float,
    smma20_history: Optional[List[float]] = None,
    smma120_history: Optional[List[float]] = None,
) -> Dict[str, float]:
    """Compute SMMA-derived features.
    
    Args:
        smma20: Current SMMA(20) value.
        smma120: Current SMMA(120) value.
        ltp: Current LTP.
        smma20_history: Recent SMMA(20) values for slope calculation.
        smma120_history: Recent SMMA(120) values for slope calculation.
        
    Returns:
        Dictionary of SMMA feature values.
    """
    s20 = smma20 or 0.0
    s120 = smma120 or 0.0
    
    smma_distance = safe_divide(s20 - s120, ltp, 0.0) if ltp > 0 else 0.0
    
    # Calculate slopes (change over last 3 bars)
    slope_20 = 0.0
    if smma20_history and len(smma20_history) >= 3:
        slope_20 = safe_divide(
            smma20_history[-1] - smma20_history[-3],
            smma20_history[-3],
            0.0
        )
    
    slope_120 = 0.0
    if smma120_history and len(smma120_history) >= 3:
        slope_120 = safe_divide(
            smma120_history[-1] - smma120_history[-3],
            smma120_history[-3],
            0.0
        )
    
    return {
        'smma20': s20,
        'smma120': s120,
        'smma_distance': smma_distance,
        'smma_slope_20': slope_20,
        'smma_slope_120': slope_120,
    }
