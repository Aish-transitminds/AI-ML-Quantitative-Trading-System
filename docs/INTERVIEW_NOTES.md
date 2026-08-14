# Interview Preparation Notes

This document provides technical justifications for architectural decisions made in the QuantumGrow system, answering potential questions in the technical interview.

## 1. Why didn't you use a random `train_test_split` for Machine Learning?
**Answer**: Random splitting on financial time-series data introduces catastrophic lookahead bias. If we randomly select trades, the model might train on data from December to predict a crossover in November. The system explicitly uses a chronological split (`X[:train_end]`) in `ml/dataset.py` to ensure the model only ever learns from the past to predict the future.

## 2. How did you prevent Lookahead Bias in feature generation?
**Answer**: By strictly tying feature extraction to the exact tick when `CrossoverDetector` fires `_prev_state != current_state`. The `FeatureEngine` takes a snapshot of the in-memory `TickStore` exactly at that second. `exit_price` and future P&L are managed strictly by the `TradeManager` when a trade closes and are used exclusively as classification labels (`profitable = 1` or `0`), never as features.

## 3. Why doesn't the system crash out of memory tracking ETQ for 1000s of stocks?
**Answer**: Because it doesn't store data indefinitely. The `TickStore` uses `collections.deque(maxlen=50000)` and actively pops ticks whose timestamps fall outside of the `TICK_BUFFER_MAX_MINUTES` (90 mins). This bounds the memory footprint strictly to what is required for the 60-minute rolling ETQ average.

## 4. Why use Python `threading` and not `asyncio` for the WebSocket?
**Answer**: The Angel One `SmartWebSocketV2` SDK relies on synchronous `websocket-client` callbacks under the hood. To prevent blocking the FastAPI event loop, the broker WebSocket operates cleanly in its own daemon thread. 

## 5. How are you bypassing Angel One's 1,000 token limit?
**Answer**: Tiered subscriptions. The `MarketDataManager` subscribes to the entire NSE equity universe in lightweight Mode 1 (LTP only). It then filters for LTP (30-500) and Liquidity (>1M). Only the small subset of qualified stocks are dynamically upgraded to Mode 3 (Full depth with Bid/Ask), conserving the 1,000 token limit.

## 6. Why did you skip SHAP values for Model Explainability?
**Answer**: The assignment explicitly marked SHAP as optional. Because `ml/explain.py` successfully implemented a deterministic, rule-based Explanation Engine that perfectly describes *why* a trade is risky or supportive by comparing real-time feature values to historical profitable distributions, adding SHAP would have needlessly bloated the computational overhead and dependency size of the final executable.
