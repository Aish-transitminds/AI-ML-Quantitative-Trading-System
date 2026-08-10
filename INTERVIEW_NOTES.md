# Interview Notes — AI/ML Stock Screener

## 1. Why SMMA instead of SMA/EMA?
SMMA (also called RMA or Modified MA) provides smoother trend identification than SMA and is less reactive to noise than EMA. It reduces false crossovers caused by market noise. SMMA's formula (1/N smoothing factor vs EMA's 2/(N+1)) gives more weight to historical data, making crossover signals more reliable for trading decisions. It's the same indicator used in RSI calculations (Wilder's Smoothing).

## 2. Why LTQ?
LTQ (Last Traded Quantity) reveals the size of individual trades happening in real-time. Unlike daily volume which is cumulative, LTQ shows whether the current market activity involves large institutional trades or small retail trades. A spike in LTQ near a crossover point could indicate institutional participation, which tends to be a stronger signal.

## 3. Why ETQ?
ETQ (Exchange Traded Quantity) bridges the gap between individual LTQ values and daily volume. By summing LTQ over 5/20/60 minute windows, we capture the intensity of trading activity at different timescales. High ETQ_5M relative to ETQ_20M suggests accelerating interest, which may predict whether a crossover will sustain.

## 4. Why 2-minute vs 5-minute LTQ?
2-minute captures immediate/reactive trading activity while 5-minute captures slightly longer-term. The ratio (ltq_avg_2m / ltq_avg_5m) acts as a momentum indicator — values > 1.0 indicate increasing activity, which often precedes sustained price moves. This is similar to MACD logic but applied to trade quantity.

## 5. Why order-book imbalance?
Order-book imbalance measures the directional pressure in the market. (bid_qty - ask_qty)/(bid_qty + ask_qty) ranges from -1 to +1. Positive values indicate buying pressure (more demand), negative indicates selling pressure. Combined with a BUY crossover, positive imbalance increases the probability of a profitable move.

## 6. Why Random Forest?
Random Forest captures non-linear relationships between features that Logistic Regression cannot. It's robust to noise, handles feature interactions automatically, provides built-in feature importance, and is relatively resistant to overfitting due to bagging. It serves as the primary model when data patterns are non-linear.

## 7. Why Logistic Regression baseline?
LR provides an interpretable baseline that reveals which features have linear relationships with profitability. Its coefficients are directly interpretable (positive = increases probability). If LR performs nearly as well as RF, the relationship is mostly linear and the simpler model should be preferred.

## 8. Why time-series split?
Market data is temporally dependent — patterns change over time (regime changes). A random train/test split would leak future information into training (e.g., a January trade in test set could share patterns with a nearby January trade in train set). Chronological split ensures the model only learns from past data, which matches real-world usage.

## 9. How was leakage prevented?
All features are computed using data available AT OR BEFORE the crossover timestamp. Exit price, future SMMA values, future LTQ/ETQ, and future returns are NEVER used as features — only as the target label. The code enforces this by computing features only from the tick_store's historical buffer, not from future data.

## 10. How is the target created?
For each crossover, we track the subsequent opposite crossover. BUY target = 1 if exit_price > entry_price. SELL target = 1 if exit_price < entry_price (since it's a short position). Only closed trades contribute to training data.

## 11. How is a crossover detected?
A state machine tracks whether SMMA20 is above or below SMMA120. Only actual state transitions (bearish→bullish or bullish→bearish) generate signals. Continuous states (SMMA20 staying above SMMA120) do NOT generate repeated signals. This prevents false duplicates.

## 12. Why is probability not certainty?
ML probability represents the model's estimated likelihood based on historical patterns. Markets are non-stationary — patterns change. The model was trained on limited data and cannot account for black swan events, regulatory changes, or unprecedented market conditions. Probability is a tool for decision-making, not a guarantee.

## 13. How was threshold selected?
Multiple thresholds (0.50 to 0.80) are evaluated on the VALIDATION set only, never the test set. The threshold maximizing F1 score is selected, balancing precision (fewer false signals) and recall (not missing profitable opportunities). The test set is only used for final reporting, never for optimization.

## 14. What are model limitations?
- Limited training data (depends on market activity)
- Non-stationary markets (model can become stale)
- Does not account for transaction costs, slippage, or market impact
- Single-timeframe analysis (1-min bars only)
- No fundamental data integration
- Assumes continuous market access (no handling of market gaps)

## 15. How would the system scale?
- Use multiple WebSocket sessions (Angel One allows 3)
- Distribute processing across worker threads/processes
- Use Redis or similar for inter-process communication
- Move to PostgreSQL for multi-user support
- Use Apache Kafka for tick streaming at scale
- Deploy on cloud with auto-scaling

## 16. How would you improve the model with more data?
- Walk-forward validation with expanding windows
- Add more features: sector momentum, market-wide indicators (NIFTY correlation)
- Ensemble methods combining multiple timeframes
- Deep learning (LSTM) for sequential pattern recognition
- Feature selection using SHAP values
- Online learning to adapt to changing market conditions

## 17. What happens during broker disconnection?
- WebSocket on_close callback is triggered
- System logs the disconnection
- Auto-reconnect logic attempts reconnection with exponential backoff
- Existing data in memory is preserved
- Historical SMMA values are maintained (not lost)
- UI shows disconnection status clearly
- No new signals are generated during disconnection

## 18. How are API credentials secured?
- Stored in .env file (never committed to git)
- .gitignore excludes .env and all credential files
- Environment variables read at runtime only
- Credentials are never logged (logger strips sensitive data)
- .env.example provides template without actual values

## 19. Why isn't an LLM required?
The system uses quantitative, rule-based explanations derived from actual feature values. An LLM would add unnecessary complexity, latency, and potential hallucination. The explanations are deterministic — they directly map feature values to human-readable descriptions. This is more reliable and auditable than LLM-generated text.

## 20. How would transaction costs affect results?
Transaction costs (brokerage, STT, GST, exchange charges, slippage) would reduce net P&L. With ~0.05-0.1% per trade round-trip for intraday, small-profit trades may become losses. The system could incorporate a minimum P&L threshold or factor costs into the ML target (profitable only if P&L > costs). This would require re-training with adjusted labels.
