# Runtime Mode Architecture

QuantumGrow supports two primary operational modes: **LIVE** and **OFFLINE (DEMO)**. 
Unlike standard applications that require a full restart to change operational modes, QuantumGrow supports **seamless runtime mode switching** via a REST API endpoint and the React UI.

## Architecture & Lifecycle

The singleton `Application` class acts as the orchestrator. It manages the global state and transitions gracefully between modes.

### 1. LIVE Mode
In Live mode, the system connects directly to the Angel One SmartAPI via WebSockets (Mode 3).
- **Data Flow**: Real-time tick data flows through the `MarketDataManager`.
- **Latency**: Sub-millisecond tick parsing, enabling instant crossover detection and ML inference.
- **Subscriptions**: Dynamically upgrades qualified stocks (based on LTP and liquidity) from Mode 1 (LTP) to Mode 3 (Full Orderbook Depth).

### 2. OFFLINE (Demo) Mode
Offline mode is designed for risk-free demonstrations, UI testing, and ML walkthroughs without requiring valid broker credentials.
- **Mock Broker**: Utilizes an `OfflineBroker` stub that simulates connections.
- **Data Injection**: Parquet-backed historical synthetic ticks are loaded directly into the state manager.
- **ML Isolation**: Trades executed in OFFLINE mode do not contaminate the database used by the LIVE ML models.

## Mode Switching Implementation

When a user switches modes via `POST /api/system/mode`:

1. **Locking**: The application acquires a `_transition_lock` to ensure thread-safe transitions.
2. **Teardown**: The existing `MarketDataManager` is gracefully stopped. Any pending WebSocket connections are closed.
3. **State Isolation**: The database tables storing trades (`crossover_trades`) and metrics (`model_metrics`) are cleared to prevent cross-contamination between synthetic and real data.
4. **Memory Reset**: Ephemeral states (such as SMMA history, `CrossoverManager`, and `ApplicationState`) are completely flushed.
5. **Re-Initialization**: The appropriate broker environment is spawned, and the background status updater threads are relaunched.
