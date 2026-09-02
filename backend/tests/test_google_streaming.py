from fastapi.testclient import TestClient

from app.main import app
from app.voice.google_streaming import google_streaming_status


def test_google_streaming_is_optional_without_credentials(monkeypatch):
    monkeypatch.setenv("NEXA_GOOGLE_STT_ENABLED", "false")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    status = google_streaming_status()
    assert status["dependency_installed"] is True
    assert status["configured"] is False
    assert status["ready"] is False


def test_google_streaming_websocket_reports_fallback_when_unconfigured(monkeypatch):
    monkeypatch.setenv("NEXA_GOOGLE_STT_ENABLED", "false")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with TestClient(app).websocket_connect("/api/voice/stt/google-stream") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "unavailable"
        assert "GOOGLE_APPLICATION_CREDENTIALS" in message["message"]
