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
            _render_stock_table(all_results, show_all=True)
        return
    
    _render_stock_table(qualified)


def _render_stock_table(results: Dict, show_all: bool = False) -> None:
    """Render the stock screening table."""
    if not results:
        st.write("No data available.")
        return
    
    rows = []
    for symbol, result in results.items():
        row = {
            'Symbol': result.symbol,
            'LTP': f"₹{result.ltp:.2f}" if result.ltp else 'N/A',
            'Bid Price': f"₹{result.bid_price:.2f}" if result.bid_price else 'N/A',
            'Bid Qty': f"{result.bid_quantity:,}" if result.bid_quantity else 'N/A',
            'Ask Price': f"₹{result.ask_price:.2f}" if result.ask_price else 'N/A',
            'Ask Qty': f"{result.ask_quantity:,}" if result.ask_quantity else 'N/A',
            'SMMA20': f"{result.smma_fast:.2f}" if result.smma_fast else 'N/A',
            'SMMA120': f"{result.smma_slow:.2f}" if result.smma_slow else 'N/A',
            'SMMA Diff': f"{result.smma_difference:.4f}" if result.smma_difference else 'N/A',
            'ETQ 5M': f"{result.etq_5m:,}" if result.etq_5m else 'N/A',
            'ETQ 20M': f"{result.etq_20m:,}" if result.etq_20m else 'N/A',
            'ETQ 60M': f"{result.etq_60m:,}" if result.etq_60m else 'N/A',
            'Avg LTP 20M': f"₹{result.avg_ltp_20m:.2f}" if result.avg_ltp_20m else 'N/A',
            'Avg LTP 60M': f"₹{result.avg_ltp_60m:.2f}" if result.avg_ltp_60m else 'N/A',
            'Signal': result.signal or '—',
            'ML Prob': f"{result.ml_probability:.0%}" if result.ml_probability is not None else 'N/A',
            'Decision': result.decision or '—',
        }
        rows.append(row)
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(len(rows) * 40 + 50, 600),
        )
        st.caption(f"Showing {len(rows)} stocks | Last refresh: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.write("No stocks to display.")
