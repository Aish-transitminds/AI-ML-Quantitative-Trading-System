"""Reusable Streamlit UI components."""
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime


def render_status_bar(status: Dict[str, Any]) -> None:
    """Render the top status bar with connection info."""
    mode = status.get('mode', 'UNKNOWN')
    is_offline = mode == 'OFFLINE'
    
    if is_offline:
        st.warning("⚠️ **OFFLINE DEMO MODE — NOT LIVE MARKET DATA**", icon="⚠️")
    
    cols = st.columns(6)
    
    with cols[0]:
        st.metric("Mode", mode)
    with cols[1]:
        broker = status.get('broker_name', 'N/A')
        connected = "✅" if status.get('broker_connected') else "❌"
        st.metric("Broker", f"{connected} {broker}")
    with cols[2]:
        st.metric("NSE Stocks", status.get('total_instruments', 0))
    with cols[3]:
        st.metric("LTP Qualified", status.get('ltp_qualified', 0))
    with cols[4]:
        st.metric("Liquidity Qualified", status.get('liquidity_qualified', 0))
    with cols[5]:
        last_tick = status.get('last_tick_time')
        if isinstance(last_tick, datetime):
            st.metric("Last Update", last_tick.strftime('%H:%M:%S'))
        elif isinstance(last_tick, str):
            st.metric("Last Update", last_tick[-8:])
        else:
            st.metric("Last Update", "N/A")


def render_signal_badge(signal: Optional[str], decision: Optional[str], probability: Optional[float]) -> str:
    """Render a signal with color coding."""
    if not signal:
        return "—"
    
    if signal == 'BUY':
        signal_str = f"🟢 {signal}"
    else:
        signal_str = f"🔴 {signal}"
    
    if decision == 'ACCEPT':
        decision_str = "✅ ACCEPT"
    elif decision == 'AVOID':
        decision_str = "❌ AVOID"
    else:
        decision_str = "⏳ PENDING"
    
    prob_str = f"{probability:.0%}" if probability is not None else "N/A"
    
    return f"{signal_str} | {prob_str} | {decision_str}"


def render_pnl(pnl: Optional[float]) -> str:
    """Render P&L with color coding."""
    if pnl is None:
        return "—"
    if pnl > 0:
        return f"🟢 +₹{pnl:.2f}"
    elif pnl < 0:
        return f"🔴 -₹{abs(pnl):.2f}"
    else:
        return f"◯ ₹{pnl:.2f}"


def render_metric_card(title: str, value: Any, delta: Optional[str] = None, delta_color: str = "normal") -> None:
    """Render a styled metric card."""
    st.metric(title, value, delta=delta, delta_color=delta_color)


def render_explanation(
    signal_type: str,
    probability: float,
    decision: str,
    reasons: List[str],
    risk_factors: List[str],
) -> None:
    """Render signal explanation box."""
    color = "green" if decision == "ACCEPT" else "red"
    
    st.subheader(f"{signal_type} SIGNAL — Probability: {probability:.0%} — {decision}")
    
    st.markdown("**Analysis:**")
    for reason in reasons:
        st.markdown(f"  {reason}")
    
    if risk_factors:
        st.markdown("**Risk Factors:**")
        for risk in risk_factors:
            st.markdown(f"  {risk}")
    
    st.markdown("---")
    st.caption("⚠️ Probability is NOT certainty. It represents the model's estimated likelihood based on historical patterns.")
