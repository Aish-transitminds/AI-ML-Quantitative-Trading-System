# QuantumGrow Architecture

This system is built as a high-performance, multithreaded quantitative screening and machine learning engine.

## Core Pipeline

### 1. Market Data Orchestration
`MarketDataManager` sits at the top of the data hierarchy, connecting via `AngelOneProvider`.
- It initiates WebSocket subscriptions in batches to respect broker rate limits.
- It manages tiered subscriptions: Lightweight LTP mode (Mode 1) for broad screening, upgrading to Full mode (Mode 3) for qualified symbols.

### 2. The Tick Store
Incoming `MarketTick` objects are validated and dropped into the thread-safe `TickStore`.
- Memory is strictly bounded using `collections.deque(maxlen=50000)`.
- A background routine prunes ticks older than 90 minutes.
- Parquet snapshots are dumped asynchronously to disk for offline ML training.

### 3. Indicator Engine
Ticks are fed into `BarBuilder`, which emits 1-minute `Bar` objects.
- `SMMACalculator` implements a recursive smoothed moving average: `SMMA = (Previous_SMMA * (N-1) + Close) / N`.
- `CrossoverDetector` acts as a finite state machine, analyzing `_prev_state` versus `current_state` to ensure signals trigger exactly once at the point of crossover.

### 4. ML Pipeline
At the exact moment of crossover, `FeatureEngine` extracts order book depth, LTP velocity, and ETQ aggregations from the `TickStore`.
- The `TradeManager` opens a virtual position.
- The ML API (`LogisticRegression`, `RandomForest`, `XGBoost`) evaluates the historical feature set using a strict chronological split (avoiding time-series lookahead bias).
- If `model.predict_proba()` exceeds `settings.ML_THRESHOLD`, the trade is accepted.

### 5. Web Dashboard
FastAPI serves the robust API and manages the WebSocket `/ws` connection.
- The UI (React/Vite) connects via WebSocket to receive real-time, zero-refresh updates on every price tick and SMMA shift.
