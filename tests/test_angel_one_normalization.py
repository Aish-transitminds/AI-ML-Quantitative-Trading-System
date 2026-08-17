import pytest
from datetime import datetime
from broker.angel_one import AngelOneProvider
from data.models import MarketTick

def test_angel_one_normalization_basic():
    provider = AngelOneProvider()
    
    # Mocking token lookup
    provider._token_to_symbol["1234"] = "TCS-EQ"
    
    parsed_tick = None
    
    def mock_callback(tick: MarketTick):
        nonlocal parsed_tick
        parsed_tick = tick
        
    provider.set_on_tick_callback(mock_callback)
    
    # Raw payload simulating Angel One Mode 3 WebSocket
    payload = {
        "token": "1234",
        "last_traded_price": 350050,
        "last_traded_quantity": 42,
        "volume_trade_for_the_day": 1500000,
        "exchange_feed_time": 1700000000,
        "best_5_data": [
            {
                "flag": 1,
                "price": 350000,
                "quantity": 100
            },
            {
                "flag": 0,
                "price": 350100,
                "quantity": 50
            }
        ]
    }
    
    provider._on_ws_data(None, payload)
    
    assert parsed_tick is not None
    assert parsed_tick.symbol == "TCS-EQ"
    assert parsed_tick.token == "1234"
    assert parsed_tick.ltp == 3500.50
    # Test LTQ vs Volume mapping
    assert parsed_tick.ltq == 42
    assert parsed_tick.volume == 1500000
    
    # Test best_5_data depth parsing
    assert parsed_tick.bid_price == 3500.00
    assert parsed_tick.bid_quantity == 100
    assert parsed_tick.ask_price == 3501.00
    assert parsed_tick.ask_quantity == 50


def test_angel_one_normalization_paisa_bug():
    provider = AngelOneProvider()
    
    parsed_tick = None
    
    def mock_callback(tick: MarketTick):
        nonlocal parsed_tick
        parsed_tick = tick
        
    provider.set_on_tick_callback(mock_callback)
    
    # Angel One bug where LTP comes in paisa, >100x the close price
    payload = {
        "token": "999",
        "last_traded_price": 50000, # 500.00 in paisa
        "close_price": 49000,       # 490.00 in paisa
        "last_traded_quantity": 10,
    }
    
    provider._on_ws_data(None, payload)
    
    assert parsed_tick is not None
    # Verify divided by 100
    assert parsed_tick.ltp == 500.00
    assert parsed_tick.close_price == 490.00
