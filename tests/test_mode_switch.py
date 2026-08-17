import pytest
from main import Application, ApplicationState
from config import settings

def test_switch_mode_offline_to_live():
    app = Application()
    # Force initial state
    settings.MODE = "OFFLINE"
    app.state = ApplicationState()
    app.state.update_status({"mode": "OFFLINE"})
    
    # Switch
    success = app.switch_mode("LIVE")
    
    assert success is True
    assert settings.MODE == "LIVE"
    assert app.state.get_snapshot()["status"]["mode"] == "LIVE"

def test_switch_mode_invalid():
    app = Application()
    app.state = ApplicationState()
    
    with pytest.raises(ValueError, match="Invalid mode"):
        app.switch_mode("INVALID_MODE")
