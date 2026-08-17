"""
Unit tests for Angel One WebSocket tick parsing and normalizations.
Uses mocked representative payloads to verify correctness without real credentials.
"""
import pytest
from datetime import datetime
from broker.angel_one import AngelOneProvider
from data.models import MarketTick

@pytest.fixture
def provider():
    p = AngelOneProvider()
    p._token_to_symbol = {"3045": "RELIANCE-EQ"}
    return p

def test_angel_one_tick_parsing(provider):
    """Test full standard tick parsing."""
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250050,
        "last_traded_quantity": 100,
        "volume_trade_for_the_day": 500000,
        "exchange_feed_time": int(datetime.now().timestamp()),
        "best_5_data": [
            {"flag": 1, "price": 250040, "quantity": 500},
            {"flag": 0, "price": 250060, "quantity": 300}
        ]
    }
    
    provider._on_ws_data(None, mock_payload)
    
    assert len(ticks) == 1
    t = ticks[0]
    assert t.symbol == "RELIANCE-EQ"
    assert t.ltp == 2500.50
    assert t.ltq == 100
    assert t.bid_price == 2500.40
    assert t.bid_quantity == 500
    assert t.ask_price == 2500.60
    assert t.ask_quantity == 300

def test_ltp_parsing_paisa_normalization(provider):
    """Test LTP normalization when price is in paisa."""
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250050,  # Paisa
        "close_price": 250000,       # Paisa
        "last_traded_quantity": 100
    }
    provider._on_ws_data(None, mock_payload)
    
    assert ticks[0].ltp == 2500.50

def test_ltq_parsing(provider):
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250000,
        "last_traded_quantity": 42
    }
    provider._on_ws_data(None, mock_payload)
    assert ticks[0].ltq == 42

def test_market_depth_parsing(provider):
    """Test bid and ask top of book parsing (Level 1)."""
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250000,
        "best_5_data": [
            {"buySellFlag": 1, "price": 249900, "quantity": 10},
            {"buySellFlag": 1, "price": 249800, "quantity": 20},
            {"buySellFlag": 0, "price": 250100, "quantity": 15},
            {"buySellFlag": 0, "price": 250200, "quantity": 25}
        ]
    }
    provider._on_ws_data(None, mock_payload)
    assert ticks[0].bid_price == 2499.0
    assert ticks[0].bid_quantity == 10
    assert ticks[0].ask_price == 2501.0
    assert ticks[0].ask_quantity == 15

def test_timestamp_parsing(provider):
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    ts = 1691316000 # Specific UNIX epoch
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250000,
        "exchange_feed_time": ts
    }
    provider._on_ws_data(None, mock_payload)
    assert ticks[0].timestamp == datetime.fromtimestamp(ts)

def test_token_mapping(provider):
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    # Send unknown token
    mock_payload = {
        "token": "9999",
        "last_traded_price": 10000,
    }
    provider._on_ws_data(None, mock_payload)
    assert ticks[0].symbol == "9999" # defaults to token if unknown

def test_missing_depth(provider):
    """Test tick parsing when best_5_data is missing (Mode 1)."""
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250000,
        # No best_5_data
    }
    provider._on_ws_data(None, mock_payload)
    assert ticks[0].bid_price == 0.0
    assert ticks[0].bid_quantity == 0
    assert ticks[0].ask_price == 0.0
    assert ticks[0].ask_quantity == 0

def test_zero_ltq(provider):
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": 250000,
        "last_traded_quantity": 0
    }
    provider._on_ws_data(None, mock_payload)
    assert ticks[0].ltq == 0

def test_malformed_payload(provider):
    ticks = []
    provider.set_on_tick_callback(lambda t: ticks.append(t))
    
    mock_payload = {
        "token": "3045",
        "last_traded_price": "invalid_string", # Invalid price type
    }
    # Should safely fail without crashing
    provider._on_ws_data(None, mock_payload)
    assert len(ticks) == 0 # Invalid tick rejected

def test_reconnect_logic(provider):
    """Test callback logic for disconnect/reconnect."""
    events = []
    provider.set_on_disconnect_callback(lambda reason: events.append("DISCONNECT"))
    provider.set_on_connect_callback(lambda: events.append("CONNECT"))
    
    provider._on_ws_close(None)
    assert events == ["DISCONNECT"]
    
    provider._on_ws_open(None)
    assert events == ["DISCONNECT", "CONNECT"]
