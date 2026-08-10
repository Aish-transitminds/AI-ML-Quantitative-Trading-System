"""Main dashboard page — displays stock screening table and system status."""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from dashboard.components import render_status_bar, render_signal_badge
from config import settings


def render_main_page(app_state: Dict[str, Any]) -> None:
    """Render the main stock screening dashboard.
    
    Args:
        app_state: Application state dictionary with:
            - status: system status dict
            - screen_results: Dict[str, StockScreenResult]
            - qualified_results: Dict[str, StockScreenResult] (liquidity-qualified only)
    """
    st.title("📊 AI/ML Stock Market Screener")
    
    # Status bar
    status = app_state.get('status', {})
    render_status_bar(status)
    
    st.divider()
    
    # Filters info
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💰 LTP Filter: ₹{settings.LTP_MIN} — ₹{settings.LTP_MAX}")
    with col2:
        st.info(f"📊 Liquidity Filter: Bid Qty > {settings.MIN_BID_QTY:,} AND Ask Qty > {settings.MIN_ASK_QTY:,}")
    
    # Main stock table
    st.subheader("🎯 Qualified Stocks")
    
    qualified = app_state.get('qualified_results', {})
    
    if not qualified:
        st.info("No stocks currently pass both LTP and liquidity filters. Waiting for market data...")
        
        # Show all LTP-qualified stocks as a preview
        all_results = app_state.get('screen_results', {})
        if all_results:
            st.subheader("🔍 LTP-Qualified Stocks (pre-liquidity filter)")
            _render_stock_grid(all_results, show_all=True)
        return
    
    _render_stock_grid(qualified)


import textwrap

def _render_stock_grid(results: Dict, show_all: bool = False) -> None:
    """Render the stock screening results as premium Grid Cards."""
    if not results:
        st.write("No data available.")
        return
    
    # We will lay out the cards in 3 columns
    cols = st.columns(3)
    
    for idx, (symbol, result) in enumerate(results.items()):
        col = cols[idx % 3]
        
        # Calculate visual metrics
        spread_pct = (result.ask_price - result.bid_price) / result.ask_price * 100 if result.ask_price else 0
        imbalance = "🟢 Buy Pressure" if result.bid_quantity > result.ask_quantity else "🔴 Sell Pressure"
        
        # Signal badge
        signal_html = ""
        if result.signal == "BUY":
            signal_html = f'<span class="signal-badge buy">📈 BUY</span>'
        elif result.signal == "SELL":
            signal_html = f'<span class="signal-badge sell">📉 SELL</span>'
            
        decision_html = ""
        if result.decision == "ACCEPT":
            decision_html = f'<span class="signal-badge accept">✓ ACCEPT ({result.ml_probability:.0%})</span>'
        elif result.decision == "AVOID":
            decision_html = f'<span class="signal-badge avoid">✕ AVOID ({result.ml_probability:.0%})</span>'
            
        with col:
            html_content = textwrap.dedent(f"""
            <div class="grid-card">
                <div class="card-header">
                    <span class="symbol-text">{result.symbol}</span>
                    <span class="price-text">₹{result.ltp:.2f}</span>
                </div>
                
                <div class="metric-row">
                    <span class="metric-label">SMMA (20 / 120)</span>
                    <span class="metric-value">{result.smma_fast:.2f} / {result.smma_slow:.2f}</span>
                </div>
                
                <div class="metric-row">
                    <span class="metric-label">Order Book</span>
                    <span class="metric-value" title="Spread: {spread_pct:.2f}%">{imbalance}</span>
                </div>
                
                <div class="metric-row">
                    <span class="metric-label">Volume (ETQ 5m/20m)</span>
                    <span class="metric-value">{result.etq_5m:,} / {result.etq_20m:,}</span>
                </div>
                
                <div class="metric-row" style="margin-top: 15px; align-items: center;">
                    {signal_html} {decision_html}
                </div>
            </div>
            """)
            st.markdown(html_content, unsafe_allow_html=True)
            
    st.caption(f"Showing {len(results)} stocks | Last refresh: {datetime.now().strftime('%H:%M:%S')}")
