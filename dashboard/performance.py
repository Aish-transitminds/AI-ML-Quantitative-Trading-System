"""Trading performance dashboard."""
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any

from dashboard.components import render_metric_card


def render_performance(app_state: Dict[str, Any]) -> None:
    """Render trading performance statistics."""
    st.title("📈 Performance Dashboard")
    
    stats = app_state.get('trade_stats', {})
    model_metrics = app_state.get('model_metrics', {})
    
    if not stats or stats.get('closed', 0) == 0:
        st.info("No closed trades yet. Performance metrics will appear after trades are completed.")
        return
    
    # Trade Statistics
    st.subheader("📊 Trade Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Crossovers", stats.get('total', 0))
        st.metric("BUY Signals", stats.get('buy_signals', 0))
    with col2:
        st.metric("Closed Trades", stats.get('closed', 0))
        st.metric("SELL Signals", stats.get('sell_signals', 0))
    with col3:
        st.metric("Profitable", stats.get('profitable', 0))
        st.metric("Losing", stats.get('losing', 0))
    with col4:
        win_rate = stats.get('win_rate', 0)
        st.metric("Win Rate", f"{win_rate:.1%}")
        st.metric("Open Trades", stats.get('open', 0))
    
    st.divider()
    
    # Financial Metrics
    st.subheader("💰 Financial Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_pnl = stats.get('total_pnl', 0)
        color = "normal" if total_pnl >= 0 else "inverse"
        st.metric("Total P&L", f"₹{total_pnl:.2f}", delta_color=color)
    with col2:
        st.metric("Average P&L", f"₹{stats.get('avg_pnl', 0):.2f}")
    with col3:
        pf = stats.get('profit_factor', 0)
        st.metric("Profit Factor", f"{pf:.2f}" if pf != float('inf') else "∞")
    with col4:
        st.metric("Max Drawdown", f"₹{stats.get('max_drawdown', 0):.2f}")
    
    st.divider()
    
    # Model Metrics
    st.subheader("🧠 Model Performance")
    
    if model_metrics:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Accuracy", f"{model_metrics.get('accuracy', 0):.2%}")
        with col2:
            st.metric("Precision", f"{model_metrics.get('precision', 0):.2%}")
        with col3:
            st.metric("Recall", f"{model_metrics.get('recall', 0):.2%}")
        with col4:
            st.metric("F1 Score", f"{model_metrics.get('f1', 0):.2%}")
        with col5:
            st.metric("ROC-AUC", f"{model_metrics.get('roc_auc', 0):.4f}")
    else:
        st.info("Model metrics will appear after ML model is trained.")
    
    # P&L Chart
    trades = app_state.get('trades', [])
    closed_trades = [t for t in trades if t.get('status') == 'CLOSED' and t.get('pnl') is not None]
    
    if closed_trades:
        st.subheader("📉 Cumulative P&L")
        
        pnls = [t['pnl'] for t in closed_trades]
        cumulative = []
        running = 0
        for p in pnls:
            running += p
            cumulative.append(running)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(cumulative) + 1)),
            y=cumulative,
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='#2ecc71' if cumulative[-1] >= 0 else '#e74c3c', width=2),
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.1)' if cumulative[-1] >= 0 else 'rgba(231, 76, 60, 0.1)',
        ))
        fig.update_layout(
            title="Cumulative P&L Curve",
            xaxis_title="Trade #",
            yaxis_title="P&L (₹)",
            height=350,
            template='plotly_dark',
        )
        st.plotly_chart(fig, use_container_width=True)
