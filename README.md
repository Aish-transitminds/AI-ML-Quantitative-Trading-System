# AI/ML Stock Market Screening and Analysis System

A production-quality full-stack application that scans NSE-listed stocks in real-time, applies quantitative screening filters, computes SMMA indicators, detects crossovers, and uses ML models to predict crossover profitability.

## Features
- **Real-time NSE Stock Scanning**: Built on Angel One SmartAPI and FYERS for live market data.
- **Quantitative Filters**: LTP filter (₹30-₹500) and liquidity filter (Bid/Ask Qty > 1M).
- **Advanced Technicals**: SMMA(20) / SMMA(120) moving average crossover detection.
- **Machine Learning Predictor**: Logistic Regression, Random Forest, XGBoost trained to predict crossover profitability.
- **Extensive Feature Engineering**: 25+ features including ETQ (Estimated Traded Quantity), LTQ, Order Imbalance, and SMMA distances.
- **State-of-the-art Web Dashboard**: Built with React, TypeScript, and Lightweight Charts for a professional, responsive UI.
- **Asynchronous Python Backend**: FastAPI-powered backend handling WebSockets, data persistence (SQLite/Parquet), and ML pipelines in real-time.
- **Offline Demo Mode**: Fully simulates live market conditions, ticks, and chart bars for evaluation purposes without needing active broker credentials.

## Architecture
```text
Broker (Angel One / FYERS / Offline Demo)
  ↓ WebSocket
Data Pipeline (MarketDataManager → TickStore)
  ↓
Bar Builder (1-minute Candlesticks)
  ↓
Indicators (SMMA 20/120) & Crossover Manager
  ↓
Feature Engine (25 custom ETQ/LTQ/Orderbook features)
  ↓
ML Predictor (LR / RF / XGBoost)
  ↓
FastAPI Server (REST + WebSockets)
  ↓
React Frontend (Vite, TypeScript, Recharts, Lightweight Charts)
```

## Technologies
- **Backend**: Python 3.10+, FastAPI, Uvicorn, scikit-learn, XGBoost, pandas, numpy, SQLite, Parquet.
- **Frontend**: React, TypeScript, Vite, React Router, Recharts, Lightweight Charts v5.

## Quick Start

### 1. Installation
```bash
git clone <repo-url>
cd "AI stock predictor"

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional, for development)
cd web
npm install
cd ..
```

### 2. Run the Application
The application includes a unified runner that serves both the API and the pre-built React frontend.

**Offline Demo Mode (Default):**
```bash
# Starts the backend, uses simulated data, and serves the UI
python run.py
```
Then navigate to `http://127.0.0.1:8000/` in your browser.

**Development Mode:**
If you want to run the React development server with hot-reloading alongside the FastAPI backend:
```bash
python run.py --dev
```

### 3. Live Mode
To run against live market data, configure your `.env` file with your broker credentials and set `MODE=LIVE`.

## Methodology Highlights

### SMMA (Smoothed Moving Average)
- Not an EMA. Formula: `SMMA_t = (SMMA_{t-1} × (N-1) + Price_t) / N`
- Computed on live 1-minute bars aggregated directly from incoming broker ticks.

### ETQ vs Volume
- **Volume**: Cumulative daily traded quantity (directly from broker).
- **LTQ (Last Traded Quantity)**: Quantity of the most recent individual trade.
- **ETQ (Estimated Traded Quantity)**: Sum of LTQ over rolling windows (5/20/60 min) to gauge short-term market momentum.

### Machine Learning
- **Target**: Profitability of a detected crossover. BUY profitable if exit > entry; SELL profitable if exit < entry.
- **Validation**: Strict chronological split (60% Train, 20% Val, 20% Test) to prevent data leakage.
- **Handling Imbalance**: Uses `class_weight='balanced'`.

## Project Structure
- `/api_server.py`: FastAPI endpoints and WebSocket routes.
- `/main.py`: Core application orchestrator, loop, and demo logic.
- `/data/`: Tick persistence, market data processing, and BarBuilder.
- `/ml/`: Feature engine, datasets, and model training (LR/RF/XGBoost).
- `/web/`: React frontend (Pages, Components, Charts, API integration).
- `/storage/`: SQLite Database manager.
- `/run.py`: Entry point for launching the system.

## Disclaimer
This is a technical assignment and research application. It does NOT guarantee profitable trading. ML predictions represent historical pattern analysis, not financial advice.
