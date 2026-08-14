# ML Methodology & Lookahead Bias Prevention

This document explains the data preparation, feature engineering, and validation methodologies employed in the QuantumGrow AI/ML Quantitative Trading System.

## Objective
The goal is to predict if a newly formed SMMA20/SMMA120 crossover will be profitable (exit > entry for BUY, exit < entry for SELL) using data strictly available *at the time of the crossover*.

## Feature Generation & Leakage Prevention
Lookahead bias occurs when future data is accidentally included in the training features. This system mathematically eliminates lookahead bias via the following constraints:

1. **Strict Temporal Feature Extraction**:
   - Features are calculated *only* when `_on_crossover_signal` fires.
   - The `FeatureEngine.compute_features` method reads from the rolling in-memory `TickStore` (which only contains past/present data) and the instant `SMMACalculator` values.
2. **Explicitly Excluded Fields**:
   - The exit price (`exit_price`), exit timestamp (`exit_timestamp`), and realized P&L (`pnl`) are exclusively managed by `TradeManager` when closing a trade.
   - These variables are never passed to `FeatureEngine`. They are used *only* as labels (`profitable = 1` or `0`) during the `DatasetBuilder` mapping phase.
3. **No Target Leakage in ETQ/LTQ**:
   - Exchange Traded Quantity (ETQ) aggregates are calculated strictly up to the current crossover timestamp using `timedelta`.

## Validation Split Strategy
To properly validate time-series financial data, random `train_test_split` cross-validation is invalid because it leaks future context into the training set (e.g., training on December to predict November).

**Implementation**:
`ml/dataset.py` implements a strict **chronological split**:
```python
# Sort chronologically
trades.sort(key=lambda t: t.entry_timestamp)

# Split indices (60% Train, 20% Val, 20% Test)
train_end = int(n * 0.6)
val_end = int(n * 0.8)

# Strict slicing prevents random leakage
X_train = X[:train_end]
X_val = X[train_end:val_end]
X_test = X[val_end:]
```

## Explanation Engine (Rule-based)
Instead of adding opaque SHAP complexity, the system uses a transparent rule-based explanation engine (`ml/explain.py`). It calculates the deviation of current features (like `etq_ratio` and `smma_diff`) against historical profitable means, surfacing exactly *why* a trade was categorized as risky or supportive.
