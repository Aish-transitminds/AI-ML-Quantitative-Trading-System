"""AI/ML Stock Market Screening and Analysis System — Streamlit Dashboard.

This is the main entry point for the application.
Run with: streamlit run app.py

The dashboard provides:
    - Real-time stock screening (LTP + liquidity filters)
    - SMMA(20)/SMMA(120) crossover detection
    - ML-based signal prediction (ACCEPT/AVOID)
    - Trade history and performance metrics
    - Model analysis and feature importance
    - Explainable decisions

IMPORTANT: In OFFLINE mode, all data is simulated for demonstration.
The banner "OFFLINE DEMO MODE — NOT LIVE MARKET DATA" is prominently displayed.
"""
import streamlit as st
import time
from datetime import datetime

# Page config must be first Streamlit command
st.set_page_config(
    page_title="AI/ML Stock Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0e1117;
    }

    /* Header styling */
    h1 {
        color: #e0e0e0 !important;
        font-weight: 700 !important;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* Status badges */
    .status-live {
        background: linear-gradient(135deg, #00b894, #00cec9);
        padding: 4px 12px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
    }

    .status-offline {
        background: linear-gradient(135deg, #fdcb6e, #e17055);
        padding: 4px 12px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
    }

    /* Table styling */
    .dataframe {
        font-size: 0.85rem !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }

    /* Warning banner for offline mode */
    .offline-banner {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-align: center;
        font-weight: 700;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }

    /* Disclaimer footer */
    .disclaimer {
        color: #666;
        font-size: 0.75rem;
        text-align: center;
        margin-top: 2rem;
        padding: 10px;
        border-top: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)


def initialize_app():
    """Initialize the application in session state."""
    if 'app_initialized' not in st.session_state:
        with st.spinner("🔄 Initializing application..."):
            from main import get_application
            app = get_application()

            try:
                app.start()
                st.session_state['app_initialized'] = True
                st.session_state['app'] = app
            except Exception as e:
                st.error(f"❌ Application initialization failed: {e}")
                st.stop()


def main():
    """Main Streamlit application."""
    # Initialize
    initialize_app()

    app = st.session_state.get('app')
    if not app:
        st.error("Application not initialized")
        st.stop()

    # Get current state snapshot
    state = app.state.get_snapshot()

    # Sidebar navigation
    with st.sidebar:
        st.title("📊 AI/ML Screener")
        st.divider()

        page = st.radio(
            "Navigation",
            [
                "🏠 Dashboard",
                "🔍 Stock Detail",
                "📜 Crossover History",
                "📈 Performance",
                "🧠 Model Analysis",
                "⚙️ Settings",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        # Status indicator
        mode = state.get('status', {}).get('mode', 'UNKNOWN')
        if mode == 'OFFLINE':
            st.markdown(
                '<div class="status-offline">⚠️ OFFLINE DEMO</div>',
                unsafe_allow_html=True,
            )
        else:
            connected = state.get('status', {}).get('broker_connected', False)
            if connected:
                st.markdown(
                    '<div class="status-live">🟢 LIVE</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="status-offline">🔴 DISCONNECTED</div>',
                    unsafe_allow_html=True,
                )

        st.divider()

        # Quick stats in sidebar
        st.caption("Quick Stats")
        st.write(f"📡 Stocks: {state.get('status', {}).get('total_instruments', 0)}")
        st.write(f"🎯 Qualified: {state.get('status', {}).get('liquidity_qualified', 0)}")
        st.write(f"📊 Trades: {state.get('trade_stats', {}).get('total', 0)}")

        if state.get('best_model_name'):
            st.write(f"🧠 Model: {state['best_model_name']}")

        # Auto-refresh control
        st.divider()
        from config import settings
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        refresh_interval = st.slider(
            "Refresh (sec)",
            min_value=1,
            max_value=30,
            value=settings.DASHBOARD_REFRESH_SECONDS,
        )

    # Render selected page
    if page == "🏠 Dashboard":
        from dashboard.main_page import render_main_page
        render_main_page(state)

    elif page == "🔍 Stock Detail":
        from dashboard.stock_detail import render_stock_detail
        render_stock_detail(state)

    elif page == "📜 Crossover History":
        from dashboard.crossover_history import render_crossover_history
        render_crossover_history(state)

    elif page == "📈 Performance":
        from dashboard.performance import render_performance
        render_performance(state)

    elif page == "🧠 Model Analysis":
        from dashboard.model_analysis import render_model_analysis
        render_model_analysis(state)

    elif page == "⚙️ Settings":
        render_settings(state)

    # Footer disclaimer
    st.markdown(
        """
        <div class="disclaimer">
        ⚠️ This is a technical assignment and research/analysis application.
        It does NOT guarantee profitable trading. All ML predictions represent
        historical pattern analysis, not financial advice.
        Predicted probabilities are NOT certainties.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


def render_settings(state: dict):
    """Settings page."""
    st.title("⚙️ Settings")

    from config import settings

    st.subheader("📋 Current Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Stock Screening**")
        st.write(f"- LTP Range: ₹{settings.LTP_MIN} — ₹{settings.LTP_MAX}")
        st.write(f"- Min Bid Qty: {settings.MIN_BID_QTY:,}")
        st.write(f"- Min Ask Qty: {settings.MIN_ASK_QTY:,}")

        st.markdown("**SMMA Parameters**")
        st.write(f"- Fast Period: {settings.SMMA_FAST_PERIOD}")
        st.write(f"- Slow Period: {settings.SMMA_SLOW_PERIOD}")
        st.write(f"- Timeframe: {settings.SMMA_TIMEFRAME}")

    with col2:
        st.markdown("**ML Configuration**")
        st.write(f"- Threshold: {settings.ML_THRESHOLD}")
        st.write(f"- Min Trades for Training: {settings.MIN_TRADES_FOR_TRAINING}")
        st.write(f"- Train/Val/Test Split: {settings.TRAIN_RATIO}/{settings.VALIDATION_RATIO}/{settings.TEST_RATIO}")

        st.markdown("**Data Management**")
        st.write(f"- Tick Buffer: {settings.TICK_BUFFER_MAX_MINUTES} minutes")
        st.write(f"- Persist Interval: {settings.TICK_PERSIST_INTERVAL_SECONDS}s")
        st.write(f"- Historical Bars Fetch: {settings.HISTORICAL_BARS_FETCH}")

    st.divider()

    # ML Threshold adjuster
    st.subheader("🎛️ Adjust ML Threshold")
    new_threshold = st.slider(
        "ML Probability Threshold",
        min_value=0.30,
        max_value=0.95,
        value=settings.ML_THRESHOLD,
        step=0.05,
        help="Signals with ML probability >= this threshold are ACCEPTED. Others are AVOIDED.",
    )

    if new_threshold != settings.ML_THRESHOLD:
        st.info(
            f"To apply threshold {new_threshold:.2f}, set ML_THRESHOLD={new_threshold} "
            f"in your .env file and restart the application."
        )

    st.divider()

    # Model retraining
    st.subheader("🔄 Model Management")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Retrain Models"):
            app = st.session_state.get('app')
            if app:
                with st.spinner("Training models..."):
                    app._train_model()
                st.success("Models retrained successfully!")
                st.rerun()

    with col2:
        if st.button("📊 Generate Demo Data"):
            with st.spinner("Generating demo data..."):
                from demo.sample_data_generator import generate_demo_dataset
                result = generate_demo_dataset(num_days=5)
            st.success(
                f"Generated data for {len(result['instruments'])} stocks, "
                f"{len(result.get('trades', []))} trades"
            )


if __name__ == "__main__":
    main()
