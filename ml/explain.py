"""Signal explainability — generates human-readable reasons.

For every accepted/rejected signal, produces:
- List of positive reasons (checkmarks)
- List of risk factors (warnings)

Reasons are derived from ACTUAL quantitative feature values.
This module does NOT use an LLM to invent explanations.

Example output:
    BUY SIGNAL — Probability: 82% — ACCEPT
    ✓ LTQ 2-minute average is significantly above 5-minute average
    ✓ Positive order-book imbalance (buying pressure)
    ✓ Positive short-term price momentum
    ⚠ Spread is elevated
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from data.models import SignalType
from utils.logging_config import get_logger

logger = get_logger("ml.explain")


def explain_signal(
    signal_type: SignalType,
    features: Dict[str, float],
    probability: float,
    threshold: float,
) -> Tuple[List[str], List[str]]:
    """Generate human-readable explanation for a signal decision.
    
    Args:
        signal_type: BUY or SELL.
        features: Feature values at crossover time.
        probability: ML probability score.
        threshold: Decision threshold.
        
    Returns:
        Tuple of (reasons, risk_factors).
        reasons: List of positive/negative reason strings.
        risk_factors: List of warning strings.
    """
    reasons = []
    risks = []
    
    is_buy = signal_type == SignalType.BUY
    
    # === LTQ Analysis ===
    ltq_ratio = features.get('ltq_ratio_2m_5m', 1.0)
    ltq_accel = features.get('ltq_acceleration', 0.0)
    
    if ltq_ratio > 1.2:
        reasons.append("✓ LTQ 2-minute average is significantly above 5-minute average (strong recent trading activity)")
    elif ltq_ratio > 1.0:
        reasons.append("✓ LTQ momentum is positive (increasing trading activity)")
    elif ltq_ratio < 0.8:
        reasons.append("✗ LTQ momentum is weak (decreasing trading activity)")
    else:
        reasons.append("○ LTQ momentum is neutral")
    
    if ltq_accel > 0.1:
        reasons.append("✓ LTQ is accelerating")
    elif ltq_accel < -0.1:
        reasons.append("✗ LTQ is decelerating")
    
    # === Order Book Analysis ===
    imbalance = features.get('order_imbalance', 0.0)
    
    if is_buy:
        if imbalance > 0.1:
            reasons.append("✓ Positive order-book imbalance (buying pressure)")
        elif imbalance < -0.1:
            reasons.append("✗ Negative order-book imbalance (selling pressure against BUY)")
        else:
            reasons.append("○ Order-book is balanced")
    else:  # SELL
        if imbalance < -0.1:
            reasons.append("✓ Negative order-book imbalance (selling pressure supports SELL)")
        elif imbalance > 0.1:
            reasons.append("✗ Positive order-book imbalance (buying pressure against SELL)")
        else:
            reasons.append("○ Order-book is balanced")
    
    # === Price Momentum ===
    return_5m = features.get('return_5m', 0.0)
    
    if is_buy:
        if return_5m > 0.002:
            reasons.append("✓ Positive short-term price momentum")
        elif return_5m < -0.002:
            reasons.append("✗ Negative short-term price momentum (against BUY direction)")
    else:
        if return_5m < -0.002:
            reasons.append("✓ Negative short-term price momentum (supports SELL)")
        elif return_5m > 0.002:
            reasons.append("✗ Positive short-term price momentum (against SELL direction)")
    
    # === SMMA Analysis ===
    smma_distance = features.get('smma_distance', 0.0)
    smma_slope_20 = features.get('smma_slope_20', 0.0)
    
    if abs(smma_distance) > 0.005:
        reasons.append(f"✓ SMMA20 is {'separating from' if abs(smma_distance) > 0.01 else 'moving away from'} SMMA120 (distance: {smma_distance:.4f})")
    else:
        reasons.append("✗ SMMA separation is weak (close to crossover point)")
    
    if is_buy and smma_slope_20 > 0:
        reasons.append("✓ SMMA20 slope is positive (upward trend)")
    elif not is_buy and smma_slope_20 < 0:
        reasons.append("✓ SMMA20 slope is negative (downward trend)")
    
    # === ETQ Analysis ===
    etq_5m = features.get('etq_5m', 0)
    etq_20m = features.get('etq_20m', 0)
    
    if etq_20m > 0 and etq_5m > (etq_20m / 4):  # 5m is > 25% of 20m
        reasons.append("✓ ETQ is increasing (high recent trading volume)")
    elif etq_5m < (etq_20m / 8) if etq_20m > 0 else False:
        reasons.append("✗ ETQ is low relative to recent history")
    
    # === Risk Factors ===
    spread_pct = features.get('spread_pct', 0.0)
    if spread_pct > 0.005:
        risks.append("⚠ Spread is elevated (higher transaction cost)")
    if spread_pct > 0.01:
        risks.append("⚠ Spread is very wide (significant slippage risk)")
    
    ltq_std = features.get('ltq_std_5m', 0.0)
    ltq_avg = features.get('ltq_avg_5m', 1.0)
    if ltq_avg > 0 and ltq_std / ltq_avg > 2.0:
        risks.append("⚠ LTQ volatility is high (inconsistent trade sizes)")
    
    if probability < threshold:
        reasons.append(f"✗ ML probability ({probability:.0%}) is below threshold ({threshold:.0%})")
    else:
        reasons.append(f"✓ ML probability ({probability:.0%}) meets threshold ({threshold:.0%})")
    
    return reasons, risks


def get_feature_explanation(
    feature_importance: Dict[str, float],
    features: Dict[str, float],
    top_n: int = 10,
) -> List[Dict[str, str]]:
    """Get top contributing features with their values.
    
    Args:
        feature_importance: Model feature importance scores.
        features: Current feature values.
        top_n: Number of top features to return.
        
    Returns:
        List of dicts with feature, importance, value, description.
    """
    descriptions = {
        'ltq_ratio_2m_5m': 'LTQ 2min/5min ratio',
        'order_imbalance': 'Order book imbalance',
        'smma_distance': 'SMMA20-SMMA120 distance',
        'return_5m': '5-minute price return',
        'etq_5m': 'ETQ (5 minutes)',
        'etq_20m': 'ETQ (20 minutes)',
        'spread_pct': 'Bid-ask spread %',
        'ltq_acceleration': 'LTQ acceleration',
        'smma_slope_20': 'SMMA20 slope',
        'ltq_avg_2m': 'LTQ 2-min average',
        'ltq_avg_5m': 'LTQ 5-min average',
        'avg_ltp_20m': 'Average LTP (20 min)',
        'avg_ltp_60m': 'Average LTP (60 min)',
        'bid_quantity': 'Bid quantity',
        'ask_quantity': 'Ask quantity',
        'return_1m': '1-minute return',
        'return_15m': '15-minute return',
    }
    
    sorted_features = sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    result = []
    for fname, importance in sorted_features:
        result.append({
            'feature': fname,
            'importance': f"{importance:.4f}",
            'value': f"{features.get(fname, 'N/A')}",
            'description': descriptions.get(fname, fname),
        })
    
    return result
