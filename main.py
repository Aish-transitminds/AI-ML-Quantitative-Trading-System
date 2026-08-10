"""Core application orchestrator for the AI/ML Stock Screener.

Coordinates all subsystems:
    1. Broker connection and market data streaming
    2. Data pipeline (tick store, bar builder)
    3. SMMA calculation and crossover detection
    4. Feature computation and ML prediction
    5. Trade management and P&L tracking
    6. State exposure for the Streamlit dashboard

Concurrency Architecture:
    Thread 1 (WebSocket): Broker SDK manages internally
    Thread 2 (Data Processor): Runs in on_tick callback (WebSocket thread)
    Thread 3 (Streamlit): Reads shared state via ApplicationState

All shared state access is thread-safe via locks and immutable snapshots.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List

from config import settings
from broker.base import MarketDataProvider
from broker.factory import create_broker
from data.models import (
    MarketTick, Bar, CrossoverSignal, Trade,
    StockScreenResult, FeatureVector, SignalType, Decision,
)
from data.instrument_manager import InstrumentManager
from data.tick_store import TickStore
from data.bar_builder import BarBuilder
from data.market_data_manager import MarketDataManager
from indicators.smma import SMMACalculator
from signals.crossover import CrossoverManager, CrossoverDetector
from signals.trade_manager import TradeManager
from features.feature_engine import FeatureEngine
from ml.train import ModelTrainer
from ml.predict import Predictor
from ml.dataset import DatasetBuilder
from ml.explain import explain_signal, get_feature_explanation
from ml.evaluate import evaluate_threshold_range
from storage.database import DatabaseManager
from utils.logging_config import get_logger
from utils.helpers import get_ist_now

logger = get_logger("main")


class ApplicationState:
    """Thread-safe shared application state for dashboard access.

    The Streamlit dashboard reads from this state object.
    The data processing pipeline writes to it.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._status: Dict[str, Any] = {}
        self._screen_results: Dict[str, StockScreenResult] = {}
        self._signal_explanations: Dict[str, Dict] = {}
        self._bars_data: Dict[str, List[Dict]] = {}
        self._trade_stats: Dict[str, Any] = {}
        self._model_results: Dict[str, Any] = {}
        self._feature_importance: Dict[str, float] = {}
        self._threshold_analysis: List[Dict] = []
        self._dataset_info: Dict[str, Any] = {}
        self._best_model_name: Optional[str] = None
        self._model_metrics: Dict[str, Any] = {}
        self._trades_list: List[Dict] = []

    def update_status(self, status: Dict[str, Any]) -> None:
        with self._lock:
            self._status = dict(status)

    def update_screen_results(self, results: Dict[str, StockScreenResult]) -> None:
        with self._lock:
            self._screen_results = dict(results)

    def update_signal_explanation(self, symbol: str, explanation: Dict) -> None:
        with self._lock:
            self._signal_explanations[symbol] = explanation

    def update_bars_data(self, symbol: str, bars: List[Dict]) -> None:
        with self._lock:
            self._bars_data[symbol] = bars

    def update_trade_stats(self, stats: Dict) -> None:
        with self._lock:
            self._trade_stats = dict(stats)

    def update_model_results(self, results: Dict) -> None:
        with self._lock:
            self._model_results = dict(results)

    def update_feature_importance(self, importance: Dict[str, float]) -> None:
        with self._lock:
            self._feature_importance = dict(importance)

    def update_threshold_analysis(self, analysis: List[Dict]) -> None:
        with self._lock:
            self._threshold_analysis = list(analysis)

    def update_dataset_info(self, info: Dict) -> None:
        with self._lock:
            self._dataset_info = dict(info)

    def update_trades_list(self, trades: List[Dict]) -> None:
        with self._lock:
            self._trades_list = list(trades)

    def set_best_model_name(self, name: str) -> None:
        with self._lock:
            self._best_model_name = name

    def set_model_metrics(self, metrics: Dict) -> None:
        with self._lock:
            self._model_metrics = dict(metrics)

    def get_snapshot(self) -> Dict[str, Any]:
        """Get a complete snapshot of the application state."""
        with self._lock:
            return {
                'status': dict(self._status),
                'screen_results': dict(self._screen_results),
                'qualified_results': {
                    sym: r for sym, r in self._screen_results.items()
                    if r.passes_ltp_filter and r.passes_liquidity_filter
                },
                'signal_explanations': dict(self._signal_explanations),
                'bars': dict(self._bars_data),
                'trade_stats': dict(self._trade_stats),
                'model_results': dict(self._model_results),
                'feature_importance': dict(self._feature_importance),
                'threshold_analysis': list(self._threshold_analysis),
                'dataset_info': dict(self._dataset_info),
                'best_model_name': self._best_model_name,
                'model_metrics': dict(self._model_metrics),
                'trades': list(self._trades_list),
                'min_trades': settings.MIN_TRADES_FOR_TRAINING,
            }


class Application:
    """Main application orchestrator."""

    def __init__(self):
        self.db = DatabaseManager()
        self.state = ApplicationState()
        self._running = False

        # Core components — initialized in start()
        self.data_manager: Optional[MarketDataManager] = None
        self.crossover_manager = CrossoverManager()
        self.trade_manager: Optional[TradeManager] = None
        self.feature_engine: Optional[FeatureEngine] = None
        self.model_trainer: Optional[ModelTrainer] = None
        self.predictor: Optional[Predictor] = None

        # SMMA history for slope calculation
        self._smma_history: Dict[str, Dict[str, List[float]]] = {}

    def start(self, mode: Optional[str] = None) -> None:
        """Start the application.

        Args:
            mode: Override mode ('LIVE' or 'OFFLINE').
        """
        actual_mode = mode or settings.MODE
        logger.info(f"Starting application in {actual_mode} mode")

        try:
            # Initialize database
            self.db.init_db()

            if actual_mode == "OFFLINE":
                self._start_offline()
            else:
                self._start_live()

            self._running = True
            logger.info("Application started successfully")

        except Exception as e:
            logger.error(f"Application startup failed: {e}", exc_info=True)
            raise

    def _start_offline(self) -> None:
        """Start in offline demo mode."""
        logger.info("Starting OFFLINE DEMO mode")

        from demo.sample_data_generator import (
            generate_demo_dataset, load_demo_instruments,
            load_demo_trades, DEMO_STOCKS,
        )

        # Generate demo data if not exists
        demo_dir = settings.DATA_DIR / "demo"
        instruments_file = demo_dir / "demo_instruments.parquet"
        if not instruments_file.exists():
            logger.info("Generating demo dataset for first time...")
            generate_demo_dataset(num_days=5)

        # Load demo instruments
        instruments = load_demo_instruments()
        if not instruments:
            instruments = DEMO_STOCKS

        # Create a dummy broker for offline mode
        from broker.base import MarketDataProvider

        class OfflineBroker(MarketDataProvider):
            """Minimal broker stub for offline mode."""
            def connect(self) -> bool:
                self._connected = True
                return True
            def disconnect(self) -> None:
                self._connected = False
            def get_instruments(self, exchange="NSE"):
                return instruments
            def subscribe(self, tokens, mode=3):
                pass
            def unsubscribe(self, tokens, mode=3):
                pass
            def get_historical_data(self, token, exchange="NSE",
                                     interval="ONE_MINUTE", from_date="",
                                     to_date=""):
                return []
            def start_websocket(self):
                pass
            def stop_websocket(self):
                pass
            def get_max_subscriptions(self):
                return 10000
            def get_broker_name(self):
                return "Offline Demo"

        broker = OfflineBroker()
        broker.connect()

        self.data_manager = MarketDataManager(broker, self.db)
        self.data_manager.instruments.load_instruments(instruments)

        # Initialize feature engine
        self.feature_engine = FeatureEngine(self.data_manager.tick_store)

        # Initialize trade manager
        self.trade_manager = TradeManager(self.db)

        # Initialize ML
        self.model_trainer = ModelTrainer(self.db)
        self.predictor = Predictor(self.model_trainer)

        # Load demo trades into database for ML training
        self._load_demo_trades()

        # Try training model from demo data
        self._train_model()

        # Load demo bars and simulate screen results
        self._load_demo_screen_results(instruments)

        # Count actual qualified instruments
        screen_results = self.data_manager._screen_results.values()
        ltp_qualified = sum(1 for r in screen_results if r.passes_ltp_filter)
        liquidity_qualified = sum(1 for r in screen_results if r.passes_liquidity_filter)

        # Update state
        self.state.update_status({
            'running': True,
            'broker_connected': True,
            'broker_name': 'Offline Demo',
            'total_instruments': len(instruments),
            'ltp_qualified': ltp_qualified,
            'liquidity_qualified': liquidity_qualified,
            'tick_count': 0,
            'last_tick_time': get_ist_now().strftime('%H:%M:%S'),
            'full_mode_subscriptions': 0,
            'mode': 'OFFLINE',
        })

    def _start_live(self) -> None:
        """Start in live mode with real broker."""
        logger.info("Starting LIVE mode")

        broker = create_broker()
        if not broker.connect():
            raise ConnectionError("Failed to connect to broker")

        self.data_manager = MarketDataManager(broker, self.db)

        if not self.data_manager.initialize():
            raise RuntimeError("Failed to initialize data manager")

        # Set up bar completion callback for SMMA
        self.data_manager.bar_builder.set_on_bar_complete(self._on_bar_complete)

        # Set up crossover callback
        self.crossover_manager.set_on_signal_callback(self._on_crossover_signal)

        # Initialize feature engine
        self.feature_engine = FeatureEngine(self.data_manager.tick_store)

        # Initialize trade manager
        self.trade_manager = TradeManager(self.db)

        # Initialize ML
        self.model_trainer = ModelTrainer(self.db)
        self.predictor = Predictor(self.model_trainer)

        # Try loading existing models
        self.model_trainer.load_models()

        # Start streaming
        self.data_manager.start_streaming()

        # Start status update thread
        threading.Thread(
            target=self._status_update_loop,
            name="StatusUpdater",
            daemon=True,
        ).start()

    def _on_bar_complete(self, symbol: str, bar: Bar) -> None:
        """Called when a 1-minute bar completes. Updates SMMA and checks crossover."""
        try:
            # Update crossover detector (which maintains SMMA internally)
            signal = self.crossover_manager.update(
                symbol, bar.close, bar.timestamp
            )

            # Track SMMA history for slope calculation
            detector = self.crossover_manager.get_detector(symbol)
            if detector and detector.is_ready:
                if symbol not in self._smma_history:
                    self._smma_history[symbol] = {'fast': [], 'slow': []}
                history = self._smma_history[symbol]
                history['fast'].append(detector.smma_fast.value)
                history['slow'].append(detector.smma_slow.value)
                # Keep last 10 values
                history['fast'] = history['fast'][-10:]
                history['slow'] = history['slow'][-10:]

                # Update screen result with SMMA
                result = self.data_manager._screen_results.get(symbol)
                if result:
                    result.smma_fast = detector.smma_fast.value
                    result.smma_slow = detector.smma_slow.value
                    if result.smma_fast and result.smma_slow:
                        result.smma_difference = (
                            (result.smma_fast - result.smma_slow) / result.ltp
                            if result.ltp > 0 else 0
                        )

            # Update ETQ and Avg LTP in screen results
            result = self.data_manager._screen_results.get(symbol)
            if result:
                ts = self.data_manager.tick_store
                result.etq_5m = ts.calculate_etq(symbol, 5)
                result.etq_20m = ts.calculate_etq(symbol, 20)
                result.etq_60m = ts.calculate_etq(symbol, 60)
                result.avg_ltp_20m = ts.calculate_avg_ltp(symbol, 20)
                result.avg_ltp_60m = ts.calculate_avg_ltp(symbol, 60)

        except Exception as e:
            logger.error(f"Error in bar complete handler for {symbol}: {e}")

    def _on_crossover_signal(self, symbol: str, signal: CrossoverSignal) -> None:
        """Called when a crossover is detected."""
        try:
            logger.info(f"Crossover signal: {signal.signal.value} for {symbol}")

            # Compute features at entry
            history = self._smma_history.get(symbol, {})
            features = self.feature_engine.compute_features(
                symbol,
                smma20=signal.smma_fast,
                smma120=signal.smma_slow,
                smma20_history=history.get('fast'),
                smma120_history=history.get('slow'),
            )
            signal.features = features

            # ML prediction
            if self.predictor and self.predictor.is_ready:
                prediction = self.predictor.predict(features)
                signal.ml_probability = prediction.get('probability')
                signal.decision = prediction.get('decision', Decision.PENDING)

                # Generate explanation
                reasons, risks = explain_signal(
                    signal.signal,
                    features,
                    signal.ml_probability or 0.0,
                    prediction.get('threshold_used', settings.ML_THRESHOLD),
                )
                signal.reasons = reasons
                signal.risk_factors = risks

                # Store explanation for dashboard
                self.state.update_signal_explanation(symbol, {
                    'reasons': reasons,
                    'risk_factors': risks,
                    'probability': signal.ml_probability,
                    'decision': signal.decision.value,
                })
            else:
                signal.decision = Decision.INSUFFICIENT_DATA

            # Update screen result
            result = self.data_manager._screen_results.get(symbol)
            if result:
                result.signal = signal.signal.value
                result.ml_probability = signal.ml_probability
                result.decision = signal.decision.value

            # Process trade
            if self.trade_manager:
                self.trade_manager.on_crossover_signal(symbol, signal)

                # Update trade stats
                stats = self.trade_manager.get_trade_stats()
                self.state.update_trade_stats(stats)

                # Update trades list for dashboard
                self._update_trades_list()

        except Exception as e:
            logger.error(f"Error processing crossover signal for {symbol}: {e}")

    def _train_model(self) -> None:
        """Train or retrain the ML model."""
        try:
            if not self.model_trainer:
                return

            dataset_builder = DatasetBuilder(self.db)
            dataset = dataset_builder.build_dataset()

            if dataset is None:
                logger.info("Insufficient data for model training")
                return

            logger.info("Training ML models...")
            results = self.model_trainer.train_all(
                X_train=dataset['X_train'],
                y_train=dataset['y_train'],
                X_val=dataset['X_val'],
                y_val=dataset['y_val'],
                X_test=dataset['X_test'],
                y_test=dataset['y_test'],
                feature_names=dataset['feature_names'],
            )

            # Save models
            self.model_trainer.save_models()
            self.model_trainer.persist_metrics()

            # Update state for dashboard
            self.state.update_model_results(results)
            self.state.update_dataset_info({
                **dataset['class_distribution'],
                **dataset['split_info'],
            })

            if self.model_trainer.best_model_name:
                self.state.set_best_model_name(self.model_trainer.best_model_name)

                # Feature importance from best model
                best_result = results.get(self.model_trainer.best_model_name, {})
                test_results = best_result.get('test', {})
                importance = test_results.get('feature_importance', {})
                self.state.update_feature_importance(importance)

                # Model metrics for dashboard
                self.state.set_model_metrics(test_results)

                # Threshold analysis
                if dataset['X_val'].shape[0] > 0:
                    thresh_analysis = evaluate_threshold_range(
                        self.model_trainer.best_model,
                        self.model_trainer.preprocessor.transform(dataset['X_val']),
                        dataset['y_val'],
                        settings.THRESHOLD_CANDIDATES,
                    )
                    self.state.update_threshold_analysis(thresh_analysis)

            logger.info("Model training complete")

        except Exception as e:
            logger.error(f"Model training failed: {e}", exc_info=True)

    def _load_demo_trades(self) -> None:
        """Load pre-generated demo trades into the database for ML training."""
        try:
            from demo.sample_data_generator import load_demo_trades

            existing = self.db.get_all_trades()
            if existing:
                logger.info(f"Database already has {len(existing)} trades")
                return

            demo_trades = load_demo_trades()
            if not demo_trades:
                logger.info("No demo trades found. Generating...")
                from demo.sample_data_generator import generate_demo_dataset
                generate_demo_dataset(num_days=5)
                demo_trades = load_demo_trades()

            for t in demo_trades:
                features_json = t.get('features_json', '{}')
                if isinstance(features_json, dict):
                    features_json = json.dumps(features_json)

                trade_id = self.db.insert_trade(
                    symbol=t.get('symbol', ''),
                    signal=t.get('signal', 'BUY'),
                    entry_timestamp=t.get('entry_timestamp', ''),
                    entry_price=t.get('entry_price', 0),
                    smma20_at_entry=t.get('smma20', 0),
                    smma120_at_entry=t.get('smma120', 0),
                    ml_probability=None,
                    ml_decision=None,
                    features_json=features_json,
                )

                if t.get('exit_price') is not None:
                    self.db.update_trade(
                        trade_id=trade_id,
                        exit_timestamp=t.get('exit_timestamp', ''),
                        exit_price=t.get('exit_price', 0),
                        pnl=t.get('pnl', 0),
                        profitable=t.get('profitable', 0),
                        status='CLOSED',
                    )

            logger.info(f"Loaded {len(demo_trades)} demo trades into database")

        except Exception as e:
            logger.error(f"Error loading demo trades: {e}")

    def _load_demo_screen_results(self, instruments: List[Dict]) -> None:
        """Create demo screen results for the dashboard."""
        import numpy as np

        rng = np.random.RandomState(42)

        for inst in instruments:
            symbol = inst['symbol']
            base_price = inst.get('base_price', 100.0)
            price = base_price * (1 + rng.normal(0, 0.02))

            result = StockScreenResult(
                symbol=symbol,
                exchange='NSE',
                token=inst['token'],
                ltp=round(price, 2),
                bid_price=round(price - 0.1, 2),
                bid_quantity=rng.randint(800000, 3000000),
                ask_price=round(price + 0.1, 2),
                ask_quantity=rng.randint(800000, 3000000),
                smma_fast=round(price * (1 + rng.normal(0, 0.005)), 2),
                smma_slow=round(price * (1 + rng.normal(0, 0.002)), 2),
                etq_5m=rng.randint(5000, 50000),
                etq_20m=rng.randint(20000, 200000),
                etq_60m=rng.randint(50000, 500000),
                avg_ltp_20m=round(price * (1 + rng.normal(0, 0.003)), 2),
                avg_ltp_60m=round(price * (1 + rng.normal(0, 0.005)), 2),
                last_update=get_ist_now(),
            )

            if result.smma_fast and result.smma_slow:
                result.smma_difference = round(
                    (result.smma_fast - result.smma_slow) / result.ltp, 6
                )

            self.data_manager._screen_results[symbol] = result

        # Update shared state
        self.state.update_screen_results(self.data_manager._screen_results)

        # Also update trade stats
        if self.trade_manager:
            stats = self.trade_manager.get_trade_stats()
            self.state.update_trade_stats(stats)
            self._update_trades_list()

    def _update_trades_list(self) -> None:
        """Update the trades list in shared state."""
        try:
            all_trades = self.db.get_all_trades()
            trades_dicts = []
            for t in all_trades:
                trades_dicts.append({
                    'symbol': t.symbol,
                    'signal': t.signal.value if isinstance(t.signal, SignalType) else t.signal,
                    'entry_timestamp': t.entry_timestamp.isoformat() if isinstance(t.entry_timestamp, datetime) else str(t.entry_timestamp),
                    'entry_price': t.entry_price,
                    'exit_timestamp': t.exit_timestamp.isoformat() if isinstance(t.exit_timestamp, datetime) else str(t.exit_timestamp) if t.exit_timestamp else None,
                    'exit_price': t.exit_price,
                    'pnl': t.pnl,
                    'profitable': t.profitable,
                    'status': t.status.value if isinstance(t.status, TradeStatus) else t.status,
                    'ml_probability': t.ml_probability,
                    'ml_decision': t.ml_decision,
                })
            self.state.update_trades_list(trades_dicts)
        except Exception as e:
            logger.error(f"Error updating trades list: {e}")

    def _status_update_loop(self) -> None:
        """Periodically update application state for the dashboard."""
        while self._running:
            try:
                if self.data_manager:
                    self.state.update_status(self.data_manager.status)
                    self.state.update_screen_results(
                        self.data_manager.get_screen_results()
                    )
                time.sleep(settings.DASHBOARD_REFRESH_SECONDS)
            except Exception as e:
                logger.error(f"Status update error: {e}")
                time.sleep(5)

    def stop(self) -> None:
        """Stop the application gracefully."""
        logger.info("Stopping application...")
        self._running = False

        if self.data_manager:
            self.data_manager.stop()

        logger.info("Application stopped")


# Global application instance (singleton for Streamlit session)
_app_instance: Optional[Application] = None
_app_lock = threading.Lock()


def get_application() -> Application:
    """Get or create the global Application instance."""
    global _app_instance
    with _app_lock:
        if _app_instance is None:
            _app_instance = Application()
        return _app_instance
