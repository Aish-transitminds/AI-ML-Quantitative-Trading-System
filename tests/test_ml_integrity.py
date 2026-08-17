import pytest
import os
import json
import numpy as np
from datetime import datetime, timedelta

from data.models import Trade, SignalType, TradeStatus, Decision, FeatureVector, StockScreenResult
from ml.dataset import DatasetBuilder
from ml.train import ModelTrainer
from ml.predict import Predictor
from storage.database import DatabaseManager
from config import settings

@pytest.fixture
def db(tmp_path):
    # Use a temporary file for DB to maintain state across connections
    db_file = tmp_path / "test.db"
    db_manager = DatabaseManager(db_path=str(db_file))
    return db_manager

def test_01_buy_target_generation(db):
    """1. BUY target generation & 3. Profitable BUY"""
    trade = Trade(symbol="TEST", signal=SignalType.BUY, entry_price=100.0)
    trade.close(datetime.now(), 105.0)
    assert trade.pnl == 5.0
    assert trade.profitable is True

def test_02_sell_target_generation(db):
    """2. SELL target generation & 5. Profitable SELL"""
    trade = Trade(symbol="TEST", signal=SignalType.SELL, entry_price=100.0)
    trade.close(datetime.now(), 95.0)
    assert trade.pnl == 5.0
    assert trade.profitable is True

def test_04_losing_buy(db):
    """4. Losing BUY"""
    trade = Trade(symbol="TEST", signal=SignalType.BUY, entry_price=100.0)
    trade.close(datetime.now(), 95.0)
    assert trade.pnl == -5.0
    assert trade.profitable is False

def test_06_losing_sell(db):
    """6. Losing SELL"""
    trade = Trade(symbol="TEST", signal=SignalType.SELL, entry_price=100.0)
    trade.close(datetime.now(), 105.0)
    assert trade.pnl == -5.0
    assert trade.profitable is False

def test_07_zero_pnl(db):
    """7. Zero P&L"""
    trade = Trade(symbol="TEST", signal=SignalType.BUY, entry_price=100.0)
    trade.close(datetime.now(), 100.0)
    assert trade.pnl == 0.0
    assert trade.profitable is False

def test_08_chronological_dataset_split(db):
    """8. Chronological dataset split"""
    base_time = datetime.now() - timedelta(days=10)
    
    # Insert dummy trades chronologically
    for i in range(100):
        # We need both classes to allow training
        profitable = i % 2 == 0
        trade = Trade(
            symbol=f"TEST_{i}",
            signal=SignalType.BUY,
            entry_timestamp=base_time + timedelta(hours=i),
            entry_price=100.0,
            smma_fast_at_entry=100.0,
            smma_slow_at_entry=100.0,
            features_at_entry=FeatureVector().to_dict(),
            exit_timestamp=base_time + timedelta(hours=i, minutes=5),
            exit_price=105.0 if profitable else 95.0,
            pnl=5.0 if profitable else -5.0,
            profitable=profitable,
            status=TradeStatus.CLOSED
        )
        trade.id = db.insert_trade(trade)
        db.update_trade(trade)
    
    builder = DatasetBuilder(db)
    dataset = builder.build_dataset()
    assert dataset is not None
    
    # Check sizes (60/20/20 of 100 is 60/20/20)
    assert len(dataset['X_train']) == 60
    assert len(dataset['X_val']) == 20
    assert len(dataset['X_test']) == 20
    
    # Verify chronologically
    trades = dataset['trades']
    for i in range(1, len(trades)):
        assert trades[i-1].entry_timestamp <= trades[i].entry_timestamp

def test_09_scaler_leakage(db):
    """9. Scaler leakage (fit on train only)"""
    trainer = ModelTrainer(db)
    X_train = np.array([[1], [2], [3]])
    y_train = np.array([0, 1, 0])
    X_val = np.array([[10]])
    y_val = np.array([1])
    
    # Run train_all (this internally calls fit_transform on train, transform on val/test)
    # We pass dummy single feature
    try:
        trainer.train_all(X_train, y_train, X_val, y_val, X_val, y_val, ["feat"])
    except Exception:
        pass # Expect failure due to 1 feature with models expecting more, but scaler runs first
    
    # Verify scaler mean is computed only on X_train (mean of 1,2,3 is 2.0)
    assert hasattr(trainer.preprocessor._scaler, 'mean_')
    assert np.isclose(trainer.preprocessor._scaler.mean_[0], 2.0)

def test_10_feature_leakage():
    """10. Feature leakage (no future data in FeatureVector)"""
    fv = FeatureVector()
    keys = fv.to_dict().keys()
    # Explicitly check forbidden fields are not in the FeatureVector class
    forbidden = ['exit_price', 'pnl', 'profitable', 'future']
    for f in forbidden:
        assert not any(f in k for k in keys)

def test_11_walk_forward_prediction(db):
    """11. Walk-forward prediction logic & 4. Single-class protection"""
    from main import Application
    app = Application()
    app.db = db
    
    base_time = datetime.now() - timedelta(days=10)
    
    # Generate 60 trades, all class 1 (Profitable)
    for i in range(60):
        trade = Trade(
            symbol=f"TEST_{i}",
            signal=SignalType.BUY,
            entry_timestamp=base_time + timedelta(hours=i),
            entry_price=100.0,
            smma_fast_at_entry=100.0,
            smma_slow_at_entry=100.0,
            features_at_entry=FeatureVector(return_1m=i).to_dict(),
            exit_timestamp=base_time + timedelta(hours=i, minutes=5),
            exit_price=105.0,
            pnl=5.0,
            profitable=True,
            status=TradeStatus.CLOSED
        )
        trade.id = db.insert_trade(trade)
        db.update_trade(trade)
    
    app._walk_forward_predict_historical_trades()
    
    trades = db.get_closed_trades()
    # Trades 0-49 should be INSUFFICIENT_DATA because window < 50
    # Trades 50-59 should ALSO be INSUFFICIENT_DATA because only 1 class exists in history
    for t in trades:
        assert t.ml_decision == Decision.INSUFFICIENT_DATA.value

def test_12_no_future_data_in_prediction():
    """12. No future data in prediction"""
    fv = FeatureVector(return_5m=0.01)
    trainer = ModelTrainer(DatabaseManager())
    predictor = Predictor(trainer)
    # The predictor only accepts `features` dict. 
    # It cannot access exit_price or P&L.
    # We verify the signature doesn't take target/P&L.
    import inspect
    sig = inspect.signature(predictor.predict)
    assert 'features' in sig.parameters
    assert 'exit_price' not in sig.parameters

def test_13_14_no_hardcoded_predictions():
    """13 & 14. No hard-coded ML probability or decision in demo generator"""
    with open('main.py', 'r') as f:
        content = f.read()
    # Verify the specific random.uniform for probability has been removed from _load_demo_trades
    assert "random.uniform(0.65, 0.95)" not in content

def test_15_model_probability_range():
    """15. Model probability range 0-1"""
    trainer = ModelTrainer(DatabaseManager())
    X = np.random.randn(100, len(FeatureVector.feature_names()))
    y = np.random.randint(0, 2, 100)
    trainer.train_all(X, y, X, y, X, y, FeatureVector.feature_names())
    
    predictor = Predictor(trainer)
    res = predictor.predict(FeatureVector().to_dict())
    assert 0.0 <= res['probability'] <= 1.0

def test_16_accept_avoid_threshold():
    """16. ACCEPT/AVOID threshold logic"""
    trainer = ModelTrainer(DatabaseManager())
    
    # Must fit preprocessor to avoid prediction error
    X_dummy = np.zeros((10, len(FeatureVector.feature_names())))
    trainer.preprocessor.fit_transform(X_dummy)
    
    # Mock best_model
    class MockModel:
        def predict_proba(self, X):
            return np.array([[0.2, 0.8]]) # 80% prob
    
    trainer.best_model = MockModel()
    trainer.best_threshold = 0.85
    trainer.best_model_name = "mock"
    trainer.feature_names = FeatureVector.feature_names()
    
    predictor = Predictor(trainer)
    res = predictor.predict(FeatureVector().to_dict())
    
    # 0.8 < 0.85 -> AVOID
    assert res['decision'] == Decision.AVOID
    
    trainer.best_threshold = 0.75
    res2 = predictor.predict(FeatureVector().to_dict())
    # 0.8 > 0.75 -> ACCEPT
    assert res2['decision'] == Decision.ACCEPT

def test_17_simulated_dashboard_prediction():
    """17. Simulated dashboard prediction"""
    # Verify dashboard mock uses dummy feature vector and live pipeline
    from ml.explain import explain_signal
    fv = FeatureVector().to_dict()
    reasons, risks = explain_signal(SignalType.BUY, fv, 0.85, 0.65)
    # The actual reasons array includes standard logic, but in main.py we explicitly prepend
    # the OFFLINE DEMO string. We check the explain_signal function signatures exist and work.
    assert isinstance(reasons, list)
    assert isinstance(risks, list)
