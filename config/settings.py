"""Centralized configuration for the AI/ML Stock Market Screening System.

All configurable parameters are defined here. No magic numbers should exist
elsewhere in the codebase.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Project Paths ===
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data_store"
RAW_TICKS_DIR = DATA_DIR / "raw_ticks"
PROCESSED_DIR = DATA_DIR / "processed"
SIGNALS_DIR = DATA_DIR / "signals"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = DATA_DIR / "screener.db"

# Create directories
for d in [DATA_DIR, RAW_TICKS_DIR, PROCESSED_DIR, SIGNALS_DIR, MODELS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === Broker Configuration ===
BROKER = os.getenv("BROKER", "angel_one")  # angel_one | fyers
API_KEY = os.getenv("API_KEY", "")
CLIENT_ID = os.getenv("CLIENT_ID", "")
PASSWORD = os.getenv("PASSWORD", "")
TOTP_SECRET = os.getenv("TOTP_SECRET", "")
FYERS_APP_ID = os.getenv("FYERS_APP_ID", "")
FYERS_SECRET = os.getenv("FYERS_SECRET", "")
FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "")

# === Mode ===
MODE = os.getenv("MODE", "OFFLINE")  # LIVE | OFFLINE

# === Stock Screening Filters ===
LTP_MIN = float(os.getenv("LTP_MIN", "30"))
LTP_MAX = float(os.getenv("LTP_MAX", "500"))
MIN_BID_QTY = int(os.getenv("MIN_BID_QTY", "1000000"))
MIN_ASK_QTY = int(os.getenv("MIN_ASK_QTY", "1000000"))

# === SMMA Parameters ===
SMMA_FAST_PERIOD = int(os.getenv("SMMA_FAST", "20"))
SMMA_SLOW_PERIOD = int(os.getenv("SMMA_SLOW", "120"))
SMMA_TIMEFRAME = "1min"  # Bar timeframe for SMMA calculation

# === ETQ Windows (minutes) ===
ETQ_WINDOWS = [5, 20, 60]

# === LTQ Windows (minutes) ===
LTQ_WINDOWS = [2, 5]

# === Average LTP Windows (minutes) ===
AVG_LTP_WINDOWS = [20, 60]

# === Return Windows (minutes) ===
RETURN_WINDOWS = [1, 5, 15]

# === ML Configuration ===
ML_THRESHOLD = float(os.getenv("ML_THRESHOLD", "0.65"))
MIN_TRADES_FOR_TRAINING = int(os.getenv("MIN_TRADES", "50"))
TRAIN_RATIO = 0.6
VALIDATION_RATIO = 0.2
TEST_RATIO = 0.2
THRESHOLD_CANDIDATES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

# === Data Management ===
TICK_BUFFER_MAX_MINUTES = 90  # Max minutes of ticks to keep in RAM per symbol
TICK_PERSIST_INTERVAL_SECONDS = 300  # Persist ticks to Parquet every N seconds
HISTORICAL_BARS_FETCH = 200  # Number of historical bars to fetch for SMMA warm-up
SUBSCRIPTION_RESCAN_INTERVAL = 300  # Re-evaluate LTP filter every N seconds

# === WebSocket ===
WS_MAX_SUBSCRIPTIONS = 1000  # Angel One limit per session
WS_RECONNECT_DELAY = 5  # Seconds before reconnect attempt
WS_MAX_RECONNECT_ATTEMPTS = 10

# === Dashboard ===
DASHBOARD_REFRESH_SECONDS = int(os.getenv("REFRESH_INTERVAL", "3"))
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}"
