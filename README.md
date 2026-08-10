# AI/ML Stock Market Screening and Analysis System

A production-quality Python application that scans NSE-listed stocks in real-time, applies quantitative screening filters, computes SMMA indicators, detects crossovers, and uses ML models to predict crossover profitability.

## Features
- Real-time NSE stock scanning via Angel One SmartAPI
- LTP filter (₹30-₹500) and liquidity filter (Bid/Ask Qty > 1M)
- SMMA(20)/SMMA(120) crossover detection
- LTQ/ETQ-based feature engineering (25 features)
- ML models: Logistic Regression, Random Forest, XGBoost
- Chronological train/val/test split (no data leakage)
- Explainable ACCEPT/AVOID decisions
- Professional Streamlit dashboard
- Offline demo mode with simulated data
- Windows EXE packaging

## Architecture
```
Broker (Angel One / FYERS)
  ↓ WebSocket
Data Pipeline (Tick Store → Bar Builder)
  ↓
Indicators (SMMA 20/120)
  ↓
Signals (Crossover Detection)
  ↓
Feature Engine (25 features)
  ↓
ML Predictor (LR / RF / XGBoost)
  ↓
Dashboard (Streamlit)
```

## Technologies
- Python 3.10+
- Angel One SmartAPI (smartapi-python)
- Streamlit (dashboard)
- scikit-learn, XGBoost (ML)
- pandas, numpy (data processing)
- SQLite (persistence)
- Parquet (tick storage)
- Plotly (charts)

## Quick Start

### 1. Clone and Install
```bash
git clone <repo-url>
cd "AI stock predictor"
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your broker credentials
```

### 3. Run (Offline Demo)
```bash
# MODE=OFFLINE is the default
streamlit run app.py
```

### 4. Run (Live Mode)
```bash
# Set MODE=LIVE and broker credentials in .env
streamlit run app.py
```

## Configuration
All parameters in `config/settings.py`:
- LTP range, liquidity thresholds
- SMMA periods (20, 120)
- ETQ/LTQ windows
- ML threshold and training parameters

## SMMA Methodology
- Smoothed Moving Average (NOT EMA)
- Formula: SMMA_t = (SMMA_{t-1} × (N-1) + Price_t) / N
- Initial SMMA = SMA of first N values
- Computed on 1-minute bars from live ticks
- SMMA(20) = fast, SMMA(120) = slow

## Crossover Detection
- BUY: SMMA20 crosses above SMMA120
- SELL: SMMA20 crosses below SMMA120
- State machine prevents duplicate signals
- Only actual transitions trigger signals

## ETQ vs Volume
- **Volume**: Cumulative daily traded quantity (from broker)
- **LTQ**: Quantity of the most recent trade
- **ETQ**: Sum of LTQ over a rolling window (5/20/60 min)
- ETQ ≠ Volume. ETQ is calculated from individual trade quantities.

## ML Methodology
- Target: Whether crossover is eventually profitable
- BUY profitable: exit_price > entry_price
- SELL profitable: exit_price < entry_price
- Chronological split: Train 60% → Val 20% → Test 20%
- No future data in features (leakage prevention)
- Class imbalance handled via class_weight='balanced'
- Threshold optimized on validation set only

## Feature Engineering (25 Features)
LTQ: current, avg_2m, avg_5m, ratio_2m_5m, acceleration, std_5m
ETQ: 5m, 20m, 60m
Price: avg_ltp_20m, avg_ltp_60m, return_1m, return_5m, return_15m
Orderbook: bid_price, bid_qty, ask_price, ask_qty, spread, spread_pct, order_imbalance
SMMA: smma20, smma120, distance, slope_20, slope_120

## P&L Calculation
- BUY P&L = exit_price - entry_price
- SELL P&L = entry_price - exit_price
- Positive = profitable, Negative = losing

## Testing
```bash
pytest tests/ -v
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Windows EXE
```bash
python build_exe.py
# Output: dist/StockScreener/StockScreener.exe
```

## Project Structure
(list all directories and key files)

## Security
- Credentials via .env (never committed)
- .gitignore excludes .env, logs, data
- No hardcoded API keys

## Known Limitations
- WebSocket limit: 1,000 tokens per session
- SMMA needs 120 bars to initialize
- ML requires 50+ closed trades
- Offline mode uses simulated data

## Disclaimer
This is a technical assignment and research application. It does NOT guarantee profitable trading. ML predictions represent historical pattern analysis, not financial advice.
