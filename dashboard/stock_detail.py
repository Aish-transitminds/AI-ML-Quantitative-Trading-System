"""Individual stock detail page."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional
from datetime import datetime

from dashboard.components import render_explanation


def render_stock_detail(app_state: Dict[str, Any]) -> None:
    """Render detailed view for a selected stock."""
    st.title("🔍 Stock Detail")
    
    # Stock selector
    all_results = app_state.get('screen_results', {})
    symbols = sorted(all_results.keys()) if all_results else []
    
    if not symbols:
        st.info("No stocks available. Waiting for market data...")
        return
    
    selected = st.selectbox("Select Stock", symbols)
    
    if not selected or selected not in all_results:
        return
    
    result = all_results[selected]
    
    # Market data
    st.subheader(f"📊 {selected} — Market Data")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("LTP", f"₹{result.ltp:.2f}")
    with col2:
        st.metric("Bid", f"₹{result.bid_price:.2f} ({result.bid_quantity:,})")
    with col3:
        st.metric("Ask", f"₹{result.ask_price:.2f} ({result.ask_quantity:,})")
    with col4:
        spread = result.ask_price - result.bid_price if result.ask_price and result.bid_price else 0
        st.metric("Spread", f"₹{spread:.2f}")
    
    # SMMA values
    st.subheader("📈 SMMA Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("SMMA(20)", f"{result.smma_fast:.2f}" if result.smma_fast else "Initializing...")
    with col2:
        st.metric("SMMA(120)", f"{result.smma_slow:.2f}" if result.smma_slow else "Initializing...")
    with col3:
        if result.smma_difference is not None:
            st.metric("Difference", f"{result.smma_difference:.4f}")
        else:
            st.metric("Difference", "N/A")
    
    # ETQ and Average LTP
    st.subheader("📊 ETQ & Average LTP")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ETQ 5M", f"{result.etq_5m:,}" if result.etq_5m else "N/A")
    with col2:
        st.metric("ETQ 20M", f"{result.etq_20m:,}" if result.etq_20m else "N/A")
    with col3:
        st.metric("ETQ 60M", f"{result.etq_60m:,}" if result.etq_60m else "N/A")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg LTP 20M", f"₹{result.avg_ltp_20m:.2f}" if result.avg_ltp_20m else "N/A")
    with col2:
        st.metric("Avg LTP 60M", f"₹{result.avg_ltp_60m:.2f}" if result.avg_ltp_60m else "N/A")
    
    # Signal & ML
    st.subheader("🧠 ML Analysis")
    if result.signal:
        st.info(f"Signal: {result.signal} | Probability: {result.ml_probability:.0%} | Decision: {result.decision}")
        
        # Show explanation if available
        signal_data = app_state.get('signal_explanations', {}).get(selected)
        if signal_data:
            render_explanation(
                signal_type=result.signal,
                probability=result.ml_probability or 0.0,
                decision=result.decision or 'PENDING',
                reasons=signal_data.get('reasons', []),
                risk_factors=signal_data.get('risk_factors', []),
            )
    else:
        st.info("No active signal for this stock")
    
    # Price chart with SMMA
    bars = app_state.get('bars', {}).get(selected, [])
    if bars:
        _render_price_chart(selected, bars)


def _render_price_chart(symbol: str, bars: List[Dict]) -> None:
    """Render price chart with SMMA overlays."""
    st.subheader("📉 Price & SMMA Chart")
    
    if not bars:
        st.info("No bar data available for charting")
        return
    
    # Extract data
    timestamps = [b.get('timestamp', i) for i, b in enumerate(bars)]
    closes = [b.get('close', 0) for b in bars]
    smma20s = [b.get('smma20') for b in bars]
    smma120s = [b.get('smma120') for b in bars]
    
    fig = make_subplots(rows=1, cols=1)
    
    fig.add_trace(go.Scatter(
        x=timestamps, y=closes,
        mode='lines', name='Close Price',
        line=dict(color='#3498db', width=1.5)
    ))
    
    # Filter None values for SMMA
    valid_smma20 = [(t, v) for t, v in zip(timestamps, smma20s) if v is not None]
    valid_smma120 = [(t, v) for t, v in zip(timestamps, smma120s) if v is not None]
    
    if valid_smma20:
        fig.add_trace(go.Scatter(
            x=[t for t, _ in valid_smma20],
            y=[v for _, v in valid_smma20],
            mode='lines', name='SMMA(20)',
            line=dict(color='#2ecc71', width=2)
        ))
    
    if valid_smma120:
        fig.add_trace(go.Scatter(
            x=[t for t, _ in valid_smma120],
            y=[v for _, v in valid_smma120],
            mode='lines', name='SMMA(120)',
            line=dict(color='#e74c3c', width=2)
        ))
    
    fig.update_layout(
        title=f"{symbol} — Price & SMMA",
        xaxis_title="Time",
        yaxis_title="Price (₹)",
        height=400,
        template='plotly_dark',
        showlegend=True,
    )
    
    st.plotly_chart(fig, use_container_width=True)
