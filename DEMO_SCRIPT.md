# Demo Script — AI/ML Stock Screener

## Pre-Recording Checklist
- [ ] Ensure .env has MODE=OFFLINE (for demo)
- [ ] Remove any personal credentials from .env
- [ ] Close any windows showing sensitive information
- [ ] Ensure application is freshly started

## Recording Steps

### 1. Launch Application (0:00 - 0:30)
```bash
streamlit run app.py
```
- Show terminal output with startup logs
- Show browser opening automatically

### 2. Dashboard Overview (0:30 - 1:30)
- Point out the **OFFLINE DEMO MODE** banner
- Show the status bar: mode, broker, stock counts
- Show filter info: LTP range, liquidity thresholds

### 3. Stock Universe (1:30 - 2:30)
- Show the main stock table
- Point out columns: Symbol, LTP, Bid/Ask, SMMA20, SMMA120
- Show ETQ columns (5M, 20M, 60M)
- Show Average LTP columns
- Show Signal, ML Probability, Decision columns

### 4. Stock Detail (2:30 - 3:30)
- Navigate to Stock Detail page
- Select a stock from dropdown
- Show market data: LTP, Bid, Ask, Spread
- Show SMMA values and chart
- Show ETQ and Average LTP metrics

### 5. ML Analysis (3:30 - 4:30)
- Navigate to Model Analysis page
- Show dataset info: samples, train/val/test split
- Show model comparison table
- Show feature importance chart
- Show confusion matrix

### 6. Crossover History (4:30 - 5:30)
- Navigate to Crossover History
- Show the trades table
- Point out BUY and SELL signals
- Show Entry/Exit prices and P&L
- Show ML Probability and Decision for each
- Use filters: by symbol, by signal type

### 7. Performance Dashboard (5:30 - 6:30)
- Navigate to Performance
- Show trade statistics: total, profitable, losing
- Show win rate
- Show financial metrics: Total P&L, Profit Factor, Max Drawdown
- Show cumulative P&L chart
- Show model performance metrics

### 8. Settings (6:30 - 7:00)
- Navigate to Settings
- Show all configuration parameters
- Show ML threshold slider
- Show model retrain button

### 9. Clean Shutdown (7:00 - 7:15)
- Return to terminal
- Press Ctrl+C to stop
- Show graceful shutdown

## Key Points to Emphasize
- Real-time architecture (even in demo mode)
- SMMA is NOT EMA
- ETQ is NOT daily volume
- No data leakage in ML
- Chronological split, not random
- Explainable decisions from quantitative features
- P&L: BUY = exit - entry, SELL = entry - exit

## NEVER Show During Recording
- API keys
- Passwords
- TOTP secrets
- Client IDs
- Personal broker account information
