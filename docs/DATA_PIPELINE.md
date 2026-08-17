# Data Pipeline & Normalization

QuantumGrow utilizes a multi-stage event-driven data pipeline to parse, process, and analyze market ticks.

## The Pipeline Stages

1. **Provider (`broker/`)**: Normalizes disparate broker payloads into a standardized `MarketTick`.
2. **Data Manager (`data/`)**: Acts as the central nervous system. Routes incoming ticks to the appropriate builders.
3. **Bar Builder**: Aggregates continuous sub-second tick streams into defined timeframes (e.g., 1-minute OHLC bars).
4. **Feature Engine**: Computes high-level quantitative features such as ETQ (Effective Trade Quantity), Order Imbalance, Spread, and SMMA (Smoothed Moving Average) crossover slopes.
5. **Crossover Manager**: Analyzes the generated signals, tracks entry prices, and dispatches validated buy/sell events.
6. **ML Inference**: Synthesizes the feature vectors and emits a probability score using the active Random Forest classifier.

## Real-Time Constraints

To prevent memory leaks during extended LIVE sessions, the pipeline relies heavily on in-memory Ring Buffers (`collections.deque`) to limit feature history. Periodic state persistence asynchronously dumps batched data directly to `.parquet` files.
