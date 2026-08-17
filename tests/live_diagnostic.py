"""
Safe Diagnostic Script for Angel One Live Connection.

This script ONLY reads market data and NEVER places orders.
It runs a limited watchlist to verify connection, authentication,
subscription, and tick reception.
"""
import sys
import time
import os
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from broker.angel_one import AngelOneProvider
from data.models import MarketTick

WATCHLIST = [
    'RELIANCE-EQ',
    'TCS-EQ',
    'INFY-EQ',
    'HDFCBANK-EQ',
    'ICICIBANK-EQ'
]

def main():
    print("=" * 40)
    print("ANGEL ONE LIVE DATA DIAGNOSTIC")
    print("=" * 40)

    # Security check
    if not settings.API_KEY or not settings.CLIENT_ID:
        print("Authentication: FAILED - Missing credentials in .env")
        print("LIVE CONNECTION: NOT-VERIFIED — REAL BROKER CREDENTIALS REQUIRED")
        return

    provider = AngelOneProvider()
    
    ticks_received = 0
    start_time = time.time()
    
    def on_tick(tick: MarketTick):
        nonlocal ticks_received
        ticks_received += 1
        print("\n" + "-" * 30)
        print(f"Symbol: {tick.symbol}")
        print(f"Token: {tick.token}")
        print(f"LTP: ₹{tick.ltp}")
        print(f"LTQ: {tick.ltq}")
        print(f"Bid Price: ₹{tick.bid_price}")
        print(f"Bid Qty: {tick.bid_quantity}")
        print(f"Ask Price: ₹{tick.ask_price}")
        print(f"Ask Qty: {tick.ask_quantity}")
        print(f"Timestamp: {tick.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    def on_connect():
        print("WebSocket: CONNECTED")
    
    def on_disconnect(reason):
        print(f"WebSocket: DISCONNECTED ({reason})")

    provider.set_on_tick_callback(on_tick)
    provider.set_on_connect_callback(on_connect)
    provider.set_on_disconnect_callback(on_disconnect)
    
    print("Attempting Authentication...")
    if not provider.connect():
        print("Authentication: FAILED")
        return
        
    print("Authentication: SUCCESS")
    
    print("Fetching Instruments...")
    instruments = provider.get_instruments("NSE")
    if not instruments:
        print("Failed to fetch instruments.")
        return
        
    symbol_to_token = {inst['symbol']: inst['token'] for inst in instruments}
    
    tokens_to_subscribe = []
    for sym in WATCHLIST:
        if sym in symbol_to_token:
            tokens_to_subscribe.append(symbol_to_token[sym])
        else:
            print(f"Warning: Symbol {sym} not found in instrument master.")
            
    if not tokens_to_subscribe:
        print("No valid tokens to subscribe to.")
        return

    print("Starting WebSocket...")
    provider.start_websocket()
    time.sleep(3) # Wait for connect callback
    
    print(f"Subscribing to tokens: {tokens_to_subscribe} (Mode 3 / FULL)")
    provider.subscribe(tokens_to_subscribe, mode=3)
    print("Subscription: SUCCESS")
    
    print("\nWaiting for ticks (15 seconds)...")
    try:
        time.sleep(15)
    except KeyboardInterrupt:
        print("Interrupted by user.")
        
    print("\n" + "=" * 40)
    print(f"Diagnostic Complete. Ticks received: {ticks_received}")
    provider.stop_websocket()
    provider.disconnect()

if __name__ == "__main__":
    main()
