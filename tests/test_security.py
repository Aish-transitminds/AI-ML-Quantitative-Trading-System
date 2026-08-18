import pytest
import os
from fastapi.testclient import TestClient
from api_server import api

client = TestClient(api)

def test_admin_auth_missing():
    response = client.post("/api/execute", json={"symbol": "AAPL", "signal": "BUY"})
    assert response.status_code == 401
    assert "Unauthorized" in response.text

def test_admin_auth_invalid():
    response = client.post("/api/execute", headers={"x-admin-key": "invalid-key"}, json={"symbol": "AAPL", "signal": "BUY"})
    assert response.status_code == 401

def test_api_keys_not_exposed_in_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    text = response.text.lower()
    assert "api_key" not in text
    assert "nvidia" not in text
    assert "password" not in text

def test_security_headers():
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"

def test_path_traversal_prevention():
    # Assuming static file server will fail safely or return index.html without giving env
    response = client.get("/../../.env")
    assert response.status_code == 200
    # It should serve index.html (React fallback), not the .env file
    assert "<html" in response.text.lower() or "not found" in response.text.lower()
    assert "API_KEY" not in response.text
