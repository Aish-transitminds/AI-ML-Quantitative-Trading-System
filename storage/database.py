"""
Database manager for SQLite storage.
Handles CRUD operations for instruments, trades, model metrics, and app state.
"""

import sqlite3
import threading
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from config import settings
from data.models import Trade
from utils.logging_config import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_db()

    def get_connection(self):
        """Get a thread-safe database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize the database schema."""
        schema = '''
        CREATE TABLE IF NOT EXISTS instruments (
            token TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            name TEXT,
            exchange TEXT DEFAULT 'NSE',
            lot_size INTEGER DEFAULT 1,
            tick_size REAL DEFAULT 0.05,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS crossover_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            signal TEXT NOT NULL CHECK(signal IN ('BUY','SELL')),
            entry_timestamp TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_timestamp TEXT,
            exit_price REAL,
            pnl REAL,
            profitable INTEGER,
            status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','CLOSED')),
            smma20_at_entry REAL,
            smma120_at_entry REAL,
            ml_probability REAL,
            ml_decision TEXT,
            features_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            trained_at TEXT NOT NULL,
            dataset_size INTEGER,
            train_size INTEGER,
            test_size INTEGER,
            accuracy REAL,
            precision_score REAL,
            recall REAL,
            f1 REAL,
            roc_auc REAL,
            best_threshold REAL,
            win_rate REAL,
            total_pnl REAL,
            profit_factor REAL,
            max_drawdown REAL,
            feature_importance_json TEXT,
            config_json TEXT
        );

        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
        CREATE INDEX IF NOT EXISTS idx_trades_symbol ON crossover_trades(symbol);
        CREATE INDEX IF NOT EXISTS idx_trades_status ON crossover_trades(status);
        CREATE INDEX IF NOT EXISTS idx_trades_signal ON crossover_trades(signal);
        '''
        
        with self._lock:
            try:
                with self.get_connection() as conn:
                    conn.executescript(schema)
                    conn.commit()
                logger.info(f"Database initialized successfully at {self.db_path}")
            except Exception as e:
                logger.error(f"Error initializing database: {e}", exc_info=True)
                raise

    def _row_to_trade(self, row: sqlite3.Row) -> Trade:
        """Convert a database row to a Trade object."""
        return Trade(
            symbol=row['symbol'],
            signal=row['signal'],
            entry_timestamp=datetime.fromisoformat(row['entry_timestamp']),
            entry_price=row['entry_price'],
            exit_timestamp=datetime.fromisoformat(row['exit_timestamp']) if row['exit_timestamp'] else None,
            exit_price=row['exit_price'],
            pnl=row['pnl'],
            profitable=bool(row['profitable']) if row['profitable'] is not None else None,
            status=row['status'],
            smma_fast_at_entry=row['smma20_at_entry'],
            smma_slow_at_entry=row['smma120_at_entry'],
            ml_probability=row['ml_probability'],
            ml_decision=row['ml_decision'],
            features_at_entry=json.loads(row['features_json']) if row['features_json'] else None,
            id=row['id']
        )

    def insert_trade(self, trade: Trade) -> int:
        """Insert a new trade into the database."""
        query = '''
        INSERT INTO crossover_trades (
            symbol, signal, entry_timestamp, entry_price, status,
            smma20_at_entry, smma120_at_entry, ml_probability, ml_decision, features_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (
                        trade.symbol,
                        trade.signal.value if hasattr(trade.signal, 'value') else trade.signal,
                        trade.entry_timestamp.isoformat() if trade.entry_timestamp else None,
                        trade.entry_price,
                        trade.status.value if hasattr(trade.status, 'value') else trade.status,
                        trade.smma_fast_at_entry,
                        trade.smma_slow_at_entry,
                        trade.ml_probability,
                        trade.ml_decision,
                        json.dumps(trade.features_at_entry) if trade.features_at_entry else None
                    ))
                    conn.commit()
                    trade_id = cursor.lastrowid
                    trade.id = trade_id
                    logger.debug(f"Inserted trade {trade_id} for {trade.symbol}")
                    return trade_id
            except Exception as e:
                logger.error(f"Error inserting trade for {trade.symbol}: {e}")
                raise

    def update_trade(self, trade: Trade):
        """Update an existing trade."""
        if not trade.id:
            raise ValueError("Trade ID is required for updating")
            
        query = '''
        UPDATE crossover_trades SET
            exit_timestamp = ?,
            exit_price = ?,
            pnl = ?,
            profitable = ?,
            status = ?
        WHERE id = ?
        '''
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (
                        trade.exit_timestamp.isoformat() if trade.exit_timestamp else None,
                        trade.exit_price,
                        trade.pnl,
                        1 if trade.profitable else 0 if trade.profitable is False else None,
                        trade.status.value if hasattr(trade.status, 'value') else trade.status,
                        trade.id
                    ))
                    conn.commit()
                    logger.debug(f"Updated trade {trade.id} for {trade.symbol}")
            except Exception as e:
                logger.error(f"Error updating trade {trade.id}: {e}")
                raise

    def get_open_trades(self) -> List[Trade]:
        """Get all open trades."""
        query = "SELECT * FROM crossover_trades WHERE status = 'OPEN'"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    return [self._row_to_trade(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting open trades: {e}")
                return []

    def get_closed_trades(self) -> List[Trade]:
        """Get all closed trades."""
        query = "SELECT * FROM crossover_trades WHERE status = 'CLOSED'"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    return [self._row_to_trade(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting closed trades: {e}")
                return []

    def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        """Get all trades for a specific symbol."""
        query = "SELECT * FROM crossover_trades WHERE symbol = ?"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (symbol,))
                    rows = cursor.fetchall()
                    return [self._row_to_trade(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting trades for {symbol}: {e}")
                return []

    def get_all_trades(self) -> List[Trade]:
        """Get all trades."""
        query = "SELECT * FROM crossover_trades ORDER BY id DESC"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    return [self._row_to_trade(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting all trades: {e}")
                return []

    def insert_model_metrics(self, metrics: Dict[str, Any]) -> int:
        """Insert model training metrics."""
        query = '''
        INSERT INTO model_metrics (
            model_name, trained_at, dataset_size, train_size, test_size,
            accuracy, precision_score, recall, f1, roc_auc, best_threshold,
            win_rate, total_pnl, profit_factor, max_drawdown,
            feature_importance_json, config_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (
                        metrics.get('model_name', 'default'),
                        metrics.get('trained_at', datetime.now().isoformat()),
                        metrics.get('dataset_size'),
                        metrics.get('train_size'),
                        metrics.get('test_size'),
                        metrics.get('accuracy'),
                        metrics.get('precision_score'),
                        metrics.get('recall'),
                        metrics.get('f1'),
                        metrics.get('roc_auc'),
                        metrics.get('best_threshold'),
                        metrics.get('win_rate'),
                        metrics.get('total_pnl'),
                        metrics.get('profit_factor'),
                        metrics.get('max_drawdown'),
                        json.dumps(metrics.get('feature_importance', {})),
                        json.dumps(metrics.get('config', {}))
                    ))
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error inserting model metrics: {e}")
                raise

    def get_latest_model_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the most recent model metrics."""
        query = "SELECT * FROM model_metrics ORDER BY id DESC LIMIT 1"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    return None
            except Exception as e:
                logger.error(f"Error getting latest model metrics: {e}")
                return None

    def upsert_instrument(self, instrument: Dict[str, Any]):
        """Insert or update an instrument."""
        query = '''
        INSERT INTO instruments (token, symbol, name, exchange, lot_size, tick_size, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(token) DO UPDATE SET
            symbol = excluded.symbol,
            name = excluded.name,
            exchange = excluded.exchange,
            lot_size = excluded.lot_size,
            tick_size = excluded.tick_size,
            updated_at = excluded.updated_at
        '''
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (
                        instrument['token'],
                        instrument['symbol'],
                        instrument.get('name', ''),
                        instrument.get('exchange', 'NSE'),
                        instrument.get('lot_size', 1),
                        instrument.get('tick_size', 0.05),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"Error upserting instrument {instrument.get('symbol')}: {e}")
                raise

    def get_instruments(self) -> List[Dict[str, Any]]:
        """Get all instruments."""
        query = "SELECT * FROM instruments"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting instruments: {e}")
                return []

    def get_state(self, key: str) -> Optional[str]:
        """Get a value from the app_state table."""
        query = "SELECT value FROM app_state WHERE key = ?"
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (key,))
                    row = cursor.fetchone()
                    return row['value'] if row else None
            except Exception as e:
                logger.error(f"Error getting state for {key}: {e}")
                return None

    def set_state(self, key: str, value: str):
        """Set a value in the app_state table."""
        query = '''
        INSERT INTO app_state (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        '''
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (key, value, datetime.now().isoformat()))
                    conn.commit()
            except Exception as e:
                logger.error(f"Error setting state for {key}: {e}")
                raise
