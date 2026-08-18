import pytest
from unittest.mock import patch, MagicMock
from services.nemotron_service import NemotronService
import os

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
        yield

@pytest.fixture
def service(mock_env):
    return NemotronService()

def test_nemotron_service_missing_key():
    with patch.dict(os.environ, clear=True):
        service = NemotronService()
        assert service.client is None
        response = service.analyze_signal("AAPL", {"ltp": 150})
        assert "temporarily unavailable" in response["summary"]
        assert "Unable to connect" in response["reasoning"]

def test_nemotron_service_successful_response(service):
    mock_client = MagicMock()
    service.client = mock_client
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '''{
        "summary": "Bullish crossover confirmed.",
        "supporting_factors": ["Price above SMMA20"],
        "risk_factors": ["Low volume"],
        "reasoning": "The ML model likely predicted a buy because of..."
    }'''
    mock_client.chat.completions.create.return_value = mock_response

    result = service.analyze_signal("AAPL", {"ltp": 150})
    
    assert result["summary"] == "Bullish crossover confirmed."
    assert "Price above SMMA20" in result["supporting_factors"]
    assert "Low volume" in result["risk_factors"]
    assert "ML model likely predicted" in result["reasoning"]

def test_nemotron_service_handles_json_error(service):
    mock_client = MagicMock()
    service.client = mock_client
    
    # Mock invalid JSON response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Not JSON"
    mock_client.chat.completions.create.return_value = mock_response

    result = service.analyze_signal("AAPL", {"ltp": 150})
    
    assert "unavailable" in result["summary"]
    assert "invalid response format" in result["reasoning"]

def test_nemotron_service_handles_api_error(service):
    mock_client = MagicMock()
    service.client = mock_client
    
    # Mock API Exception
    mock_client.chat.completions.create.side_effect = Exception("API Timeout")

    result = service.analyze_signal("AAPL", {"ltp": 150})
    
    assert "unavailable" in result["summary"]
    assert "Unable to connect" in result["reasoning"]
