"""Crossover history page — displays all historical trades."""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from dashboard.components import render_pnl


def render_crossover_history(app_state: Dict[str, Any]) -> None:
    """Render crossover history table with filters."""
    st.title("📜 Crossover History")
    
    trades = app_state.get('trades', [])
    
    if not trades:
        st.info("No crossover trades recorded yet. Trades will appear here when SMMA crossovers are detected.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbols = sorted(set(t.get('symbol', '') for t in trades))
        selected_symbol = st.selectbox("Symbol", ['All'] + symbols)
    
    with col2:
        selected_signal = st.selectbox("Signal", ['All', 'BUY', 'SELL'])
    
    with col3:
        selected_decision = st.selectbox("Decision", ['All', 'ACCEPT', 'AVOID'])
    
    # Apply filters
    filtered = trades
    if selected_symbol != 'All':
        filtered = [t for t in filtered if t.get('symbol') == selected_symbol]
    if selected_signal != 'All':
        filtered = [t for t in filtered if t.get('signal') == selected_signal]
    if selected_decision != 'All':
        filtered = [t for t in filtered if t.get('ml_decision') == selected_decision]
    
    # Display table
    if not filtered:
        st.info("No trades match the selected filters.")
        return
    
    rows = []
    for t in filtered:
        pnl = t.get('pnl')
        rows.append({
            'Symbol': t.get('symbol', ''),
            'Time': t.get('entry_timestamp', '')[:19] if t.get('entry_timestamp') else '',
            'Signal': t.get('signal', ''),
            'Entry Price': f"₹{t.get('entry_price', 0):.2f}",
            'Exit Price': f"₹{t.get('exit_price', 0):.2f}" if t.get('exit_price') else 'OPEN',
            'P&L': f"₹{pnl:.2f}" if pnl is not None else 'OPEN',
            'Profitable': '✅' if t.get('profitable') else ('❌' if t.get('profitable') is not None and not t.get('profitable') else '⏳'),
            'ML Prob': f"{t.get('ml_probability', 0):.0%}" if t.get('ml_probability') is not None else 'N/A',
            'Decision': t.get('ml_decision', 'N/A'),
            'Status': t.get('status', 'OPEN'),
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered)} of {len(trades)} trades")
