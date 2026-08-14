# QuantumGrow Screen Recording Demo Script

This script is designed for your required 3-5 minute technical demonstration video.

## Preparation
1. Start the application: `python run.py --port 8000`.
2. Ensure it boots into "OFFLINE DEMO" mode if you do not have live Angel One credentials enabled.
3. Open the UI in Chrome at `http://localhost:8000`.

## 1. Introduction (30 seconds)
*   **Action**: Show the main Explore page and toggle the Pro Mode switch.
*   **Script**: "Hi, this is my submission for the AI/ML Quantitative Trading System assignment. Here is the QuantumGrow dashboard. By default, it's an accessible retail view, but toggling Pro Mode exposes the institutional market data and ML tools."

## 2. Market Data & Filtering (1 minute)
*   **Action**: Navigate to `Market Data`. Show the green/amber LIVE/OFFLINE badge in the header. Show the table.
*   **Script**: "The system ingests WebSocket data from the broker. You can see the LTP and liquidity filtering working in real-time. Only stocks priced between 30 and 500 INR with over 1 Million Bid/Ask quantity are upgraded to Mode 3 full-depth subscription to preserve broker rate limits."

## 3. SMMA & Feature Generation (1 minute)
*   **Action**: Expand a row in the Market Data table to show the inline Lightweight Chart.
*   **Script**: "Here we calculate the SMMA20 and SMMA120 accurately on 1-minute bars, avoiding standard EMAs per the requirements. When a crossover occurs, our Feature Engine instantly extracts the current Exchange Traded Quantity (ETQ) averages for 5, 20, and 60 minutes from our time-bounded, rolling `TickStore` memory. It also extracts Order Book Bid/Ask spreads and imbalances. Crucially, zero future data is included at this timestamp, preventing lookahead bias."

## 4. ML Validation & Trades (1 minute)
*   **Action**: Navigate to `AI Lab` or `Trade Logs`.
*   **Script**: "The dataset is strictly split chronologically (60/20/20) to prevent time-series data leakage—random train-test splits are disabled. As crossovers occur, the Logistic Regression, Random Forest, and XGBoost models output a probability of profitability. If it exceeds our strict threshold, the trade is accepted. You can see the active P&L updating on open positions here in the Trade Logs."

## 5. Conclusion (30 seconds)
*   **Action**: Show the `ASSIGNMENT_COMPLIANCE.md` in the IDE.
*   **Script**: "The complete assignment compliance matrix and architectural documentation, including the Parquet data pipeline and broker reconnection logic, is available in the `docs` directory. Thank you for your time."
