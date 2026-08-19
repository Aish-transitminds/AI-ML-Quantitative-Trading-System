"""Sample data generator for offline demo mode.

Generates realistic-looking stock market data for demonstration.
This data is SIMULATED and NOT real market data.

The generator creates:
- Tick data for ~10 sample NSE stocks in the ₹30-₹500 range
- Price series with realistic volatility and trends
- LTQ values with realistic distribution
- Bid/Ask with realistic spreads
- Enough SMMA crossovers for ML training demonstration (~50+ trades)

IMPORTANT: All generated data is clearly labeled as simulated.
Never present this data as real market data.
"""
from __future__ import annotations

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path

import numpy as np
import pandas as pd

from data.models import MarketTick, Bar, Trade, SignalType, TradeStatus
from indicators.smma import SMMACalculator
from config import settings
from utils.logging_config import get_logger

logger = get_logger("demo.generator")

# Sample NSE stocks for demo (real symbols for Yahoo Finance integration)
DEMO_STOCKS = [
    {'symbol': 'SBIN', 'token': '3045', 'name': 'State Bank of India', 'base_price': 250.0},
    {'symbol': 'TATAMOTORS', 'token': '3456', 'name': 'Tata Motors', 'base_price': 400.0},
    {'symbol': 'PNB', 'token': '2730', 'name': 'Punjab National Bank', 'base_price': 65.0},
    {'symbol': 'BANKBARODA', 'token': '4668', 'name': 'Bank of Baroda', 'base_price': 120.0},
    {'symbol': 'SAIL', 'token': '2963', 'name': 'Steel Authority of India', 'base_price': 85.0},
    {'symbol': 'COALINDIA', 'token': '20374', 'name': 'Coal India', 'base_price': 235.0},
    {'symbol': 'NHPC', 'token': '14077', 'name': 'NHPC', 'base_price': 48.0},
    {'symbol': 'IRFC', 'token': '26424', 'name': 'IRFC', 'base_price': 75.0},
    {'symbol': 'IOC', 'token': '1624', 'name': 'Indian Oil Corp', 'base_price': 95.0},
    {'symbol': 'BHEL', 'token': '438', 'name': 'Bharat Heavy Electricals', 'base_price': 155.0},
]


def generate_price_series(
    base_price: float,
    num_bars: int = 500,
    volatility: float = 0.001,
    trend: float = 0.0,
    seed: int = None,
) -> List[Dict]:
    """Generate a realistic OHLCV price series.
    
    Uses geometric Brownian motion with mean-reverting properties
    to generate prices that stay in a realistic range.
    """
    if seed is not None:
        rng = np.random.RandomState(seed)
    else:
        rng = np.random.RandomState()
    
    bars = []
    price = base_price
    
    for i in range(num_bars):
        # Random returns with slight mean reversion
        mean_rev = -0.001 * (price - base_price) / base_price
        ret = rng.normal(trend + mean_rev, volatility)
        
        # Generate OHLC
        open_price = price
        intra_vol = abs(rng.normal(0, volatility * 2))
        
        high = open_price * (1 + intra_vol)
        low = open_price * (1 - intra_vol)
        close = open_price * (1 + ret)
        
        # Ensure OHLC consistency
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Volume with some randomness
        base_vol = rng.randint(5000, 50000)
        volume = int(base_vol * (1 + abs(ret) * 50))  # Higher volume on big moves
        
        bars.append({
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume,
        })
        
        price = close
    
    return bars


def generate_tick_data(
    symbol: str,
    token: str,
    bars: List[Dict],
    start_time: datetime,
    ticks_per_bar: int = 10,
) -> List[MarketTick]:
    """Generate tick-level data from 1-minute bars."""
    ticks = []
    current_time = start_time
    rng = np.random.RandomState(hash(symbol) % 2**31)
    
    for bar in bars:
        bar_open = bar['open']
        bar_close = bar['close']
        bar_high = bar['high']
        bar_low = bar['low']
        
        # Generate ticks within this bar
        for j in range(ticks_per_bar):
            # Interpolate price within bar
            t = j / ticks_per_bar
            price = bar_open + (bar_close - bar_open) * t
            price += rng.normal(0, (bar_high - bar_low) * 0.1)
            price = max(bar_low, min(bar_high, price))
            price = round(price, 2)
            
            # Generate LTQ with realistic distribution (log-normal)
            ltq = max(1, int(rng.lognormal(3, 1.5)))  # Typical range: 1-1000+
            
            # Generate bid/ask
            spread = max(0.05, round(price * rng.uniform(0.0005, 0.003), 2))
            bid_price = round(price - spread / 2, 2)
            ask_price = round(price + spread / 2, 2)
            
            # Generate quantities (sometimes > 1M for liquidity filter)
            bid_qty = int(rng.lognormal(12, 2))  # Can be > 1M
            ask_qty = int(rng.lognormal(12, 2))
            
            tick_time = current_time + timedelta(seconds=j * (60 / ticks_per_bar))
            
            tick = MarketTick(
                timestamp=tick_time,
                symbol=symbol,
                token=token,
                ltp=price,
                ltq=ltq,
                volume=bar['volume'],
                open_price=bar_open,
                high_price=bar_high,
                low_price=bar_low,
                close_price=bars[0]['close'] if bars else price,  # Previous close
                bid_price=bid_price,
                bid_quantity=bid_qty,
                ask_price=ask_price,
                ask_quantity=ask_qty,
                total_buy_quantity=bid_qty * 3,
                total_sell_quantity=ask_qty * 3,
            )
            ticks.append(tick)
        
        current_time += timedelta(minutes=1)
    
    return ticks

def _try_fetch_yahoo_bars(symbol: str) -> List[Dict]:
    """Try to fetch real bar data from Yahoo Finance.
    
    Returns list of bar dicts or empty list if unavailable.
    """
    try:
        import yfinance as yf
        yahoo_symbol = f"{symbol}.NS"
        ticker = yf.Ticker(yahoo_symbol)
        # Fetch 6 months of daily data for ML training
        df = ticker.history(period="6mo", interval="1d")
        
        if df.empty:
            return []
        
        bars = []
        for _, row in df.iterrows():
            bars.append({
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
            })
        
        return bars
    except ImportError:
        logger.info("yfinance not installed, falling back to synthetic data")
        return []
    except Exception as e:
        logger.warning(f"Yahoo Finance fetch failed for {symbol}: {e}")
        return []


def generate_demo_dataset(
    num_days: int = 5,
    output_dir: Path = None,
) -> Dict:
    """Generate complete demo dataset.
    
    Creates tick data, bars, and pre-computed crossover trades
    for offline demonstration.
    
    Returns:
        Dictionary with stocks, ticks, bars, and instruments.
    """
    if output_dir is None:
        output_dir = settings.DATA_DIR / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating demo dataset for {len(DEMO_STOCKS)} stocks, {num_days} days")
    
    all_instruments = []
    all_bars = {}  # symbol -> list of bar dicts
    
    # Generate data for each stock
    for stock in DEMO_STOCKS:
        symbol = stock['symbol']
        token = stock['token']
        base_price = stock['base_price']
        
        # Try to fetch real data from Yahoo Finance first
        bars = _try_fetch_yahoo_bars(symbol)
        
        if not bars:
            # Fallback to synthetic data
            logger.info(f"Yahoo Finance unavailable for {symbol}, using synthetic data")
            num_bars = 375 * num_days
            seed = hash(symbol) % 2**31
            trend = random.uniform(-0.0001, 0.0001)
            bars = generate_price_series(
                base_price, num_bars, volatility=0.001, trend=trend, seed=seed
            )
        else:
            logger.info(f"Using real Yahoo Finance data for {symbol}: {len(bars)} bars")
        
        all_bars[symbol] = bars
        
        # Create instrument entry
        all_instruments.append({
            'token': token,
            'symbol': symbol,
            'name': stock['name'],
            'exchange': 'NSE',
            'lot_size': 1,
            'tick_size': 0.05,
        })
        
        # Save bars as parquet
        start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0) - timedelta(days=num_days)
        bar_records = []
        current_time = start_time
        
        for bar in bars:
            # Skip non-market hours
            if current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 15):
                current_time = current_time.replace(hour=9, minute=15)
            if current_time.hour >= 15 and current_time.minute > 30:
                current_time = (current_time + timedelta(days=1)).replace(hour=9, minute=15)
            # Skip weekends
            while current_time.weekday() >= 5:
                current_time += timedelta(days=1)
            
            bar_records.append({
                'timestamp': current_time,
                'symbol': symbol,
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume'],
            })
            current_time += timedelta(minutes=1)
        
        df = pd.DataFrame(bar_records)
        safe_sym = symbol.replace('-', '_')
        df.to_parquet(output_dir / f"{safe_sym}_bars.parquet", index=False)
    
    # Save instruments
    instruments_df = pd.DataFrame(all_instruments)
    instruments_df.to_parquet(output_dir / "demo_instruments.parquet", index=False)
    
    # Generate crossover trades from the bar data
    trades = _generate_crossover_trades(all_bars)
    if trades:
        trades_records = []
        for t in trades:
            trades_records.append({
                'symbol': t['symbol'],
                'signal': t['signal'],
                'entry_timestamp': t['entry_timestamp'],
                'entry_price': t['entry_price'],
                'exit_timestamp': t['exit_timestamp'],
                'exit_price': t['exit_price'],
                'pnl': t['pnl'],
                'profitable': t['profitable'],
                'features_json': json.dumps(t.get('features', {})),
            })
        trades_df = pd.DataFrame(trades_records)
        trades_df.to_parquet(output_dir / "demo_trades.parquet", index=False)
        logger.info(f"Generated {len(trades)} demo crossover trades")
    
    logger.info(f"Demo dataset saved to {output_dir}")
    
    return {
        'instruments': all_instruments,
        'bars': all_bars,
        'trades': trades,
        'output_dir': str(output_dir),
    }


def _generate_crossover_trades(all_bars: Dict) -> List[Dict]:
    """Generate crossover trades from bar data."""
    from indicators.smma import SMMACalculator
    
    trades = []
    rng = np.random.RandomState(42)
    
    for symbol, bars in all_bars.items():
        smma20 = SMMACalculator(20)
        smma120 = SMMACalculator(120)
        
        prev_state = None  # None, 'bullish', 'bearish'
        open_trade = None
        
        start_time = datetime.now().replace(hour=9, minute=15) - timedelta(days=5)
        
        for i, bar in enumerate(bars):
            price = bar['close']
            s20 = smma20.update(price)
            s120 = smma120.update(price)
            
            if s20 is None or s120 is None:
                continue
            
            current_state = 'bullish' if s20 > s120 else 'bearish'
            ts = start_time + timedelta(minutes=i)
            
            if prev_state is not None and current_state != prev_state:
                # Close existing trade
                if open_trade:
                    signal = open_trade['signal']
                    if signal == 'BUY':
                        pnl = price - open_trade['entry_price']
                    else:
                        pnl = open_trade['entry_price'] - price
                    
                    open_trade['exit_timestamp'] = ts.isoformat()
                    open_trade['exit_price'] = price
                    open_trade['pnl'] = round(pnl, 2)
                    open_trade['profitable'] = 1 if pnl > 0 else 0
                    trades.append(open_trade)
                
                # Open new trade
                signal_type = 'BUY' if current_state == 'bullish' else 'SELL'
                
                # Generate feature values
                features = {
                    'ltq_current': float(rng.lognormal(3, 1)),
                    'ltq_avg_2m': float(rng.lognormal(3, 0.5)),
                    'ltq_avg_5m': float(rng.lognormal(3, 0.5)),
                    'ltq_ratio_2m_5m': float(rng.uniform(0.5, 2.0)),
                    'ltq_acceleration': float(rng.normal(0, 0.3)),
                    'ltq_std_5m': float(rng.lognormal(2, 1)),
                    'etq_5m': float(rng.randint(1000, 100000)),
                    'etq_20m': float(rng.randint(5000, 500000)),
                    'etq_60m': float(rng.randint(10000, 1000000)),
                    'avg_ltp_20m': price * (1 + rng.normal(0, 0.005)),
                    'avg_ltp_60m': price * (1 + rng.normal(0, 0.01)),
                    'return_1m': float(rng.normal(0, 0.002)),
                    'return_5m': float(rng.normal(0, 0.005)),
                    'return_15m': float(rng.normal(0, 0.01)),
                    'bid_price': price - 0.1,
                    'bid_quantity': float(rng.randint(500000, 3000000)),
                    'ask_price': price + 0.1,
                    'ask_quantity': float(rng.randint(500000, 3000000)),
                    'spread': 0.2,
                    'spread_pct': 0.2 / price,
                    'order_imbalance': float(rng.uniform(-0.5, 0.5)),
                    'smma20': s20,
                    'smma120': s120,
                    'smma_distance': (s20 - s120) / price,
                    'smma_slope_20': float(rng.normal(0, 0.001)),
                    'smma_slope_120': float(rng.normal(0, 0.0005)),
                }
                
                open_trade = {
                    'symbol': symbol,
                    'signal': signal_type,
                    'entry_timestamp': ts.isoformat(),
                    'entry_price': price,
                    'smma20': s20,
                    'smma120': s120,
                    'features': features,
                }
            
            prev_state = current_state
    
    return trades


def load_demo_instruments(data_dir: Path = None) -> List[Dict]:
    """Load demo instruments."""
    if data_dir is None:
        data_dir = settings.DATA_DIR / "demo"
    
    parquet_path = data_dir / "demo_instruments.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        return df.to_dict('records')
    
    # Fall back to hardcoded list
    return DEMO_STOCKS


def load_demo_bars(symbol: str, data_dir: Path = None) -> List[Dict]:
    """Load demo bar data for a symbol."""
    if data_dir is None:
        data_dir = settings.DATA_DIR / "demo"
    
    safe_sym = symbol.replace('-', '_')
    parquet_path = data_dir / f"{safe_sym}_bars.parquet"
    
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        return df.to_dict('records')
    
    return []


def load_demo_trades(data_dir: Path = None) -> List[Dict]:
    """Load pre-generated demo trades."""
    if data_dir is None:
        data_dir = settings.DATA_DIR / "demo"
    
    parquet_path = data_dir / "demo_trades.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        return df.to_dict('records')
    
    return []


if __name__ == '__main__':
    """Run directly to generate demo data."""
    print("Generating demo dataset...")
    result = generate_demo_dataset(num_days=5)
    print(f"Generated data for {len(result['instruments'])} stocks")
    print(f"Generated {len(result.get('trades', []))} crossover trades")
    print(f"Saved to: {result['output_dir']}")
