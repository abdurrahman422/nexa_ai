from __future__ import annotations

import json

import pytest

from fastapi.testclient import TestClient

from app.audit import event_log
from app.chat import service as chat_service
from app.contacts import store as contact_store
from app.main import app
from app.permissions import store as permission_store
from app.tools import whatsapp_sender
from app.tools.whatsapp_sender import WhatsAppSendResult


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(permission_store, "PERMISSIONS_FILE", tmp_path / "permissions.json")
    monkeypatch.setattr(event_log, "AUDIT_DB_PATH", tmp_path / "audit.sqlite3")
    monkeypatch.setattr(contact_store, "CONTACTS_FILE", tmp_path / "whatsapp_contacts.json")
    monkeypatch.setattr(whatsapp_sender, "LEDGER_FILE", tmp_path / "send-ledger.json")
    monkeypatch.setattr(whatsapp_sender, "PROFILE_DIR", tmp_path / "profile")
    return TestClient(app)


def _enable_send(monkeypatch) -> None:
    monkeypatch.setattr(
        chat_service,
        "is_permission_enabled",
        lambda key: key in {"whatsapp_draft_skill", "trusted_whatsapp_draft_auto_open", "whatsapp_send_skill"},
    )


def _save_rahim(client: TestClient) -> None:
    contact_store.save_contact("Rahim", "01712345678")


def test_explicit_english_send_uses_exact_text_and_request_id(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _enable_send(monkeypatch)
    _save_rahim(client)
    calls: list[tuple[str, str, str]] = []

    def fake_send(request_id: str, phone: str, text: str) -> WhatsAppSendResult:
        calls.append((request_id, phone, text))
        return WhatsAppSendResult("submitted", "Submitted for sending.")

    monkeypatch.setattr(chat_service, "send_whatsapp_message", fake_send)
    response = client.post(
        "/api/chat/message",
        json={
            "request_id": "turn-1",
            "message": "Send a WhatsApp message to Rahim saying I will call tomorrow.",
        },
    )

    data = response.json()
    assert data["intent"] == "whatsapp_send"
    assert data["status"] == "submitted"
    assert calls == [("turn-1", "8801712345678", "I will call tomorrow.")]


def test_draft_never_calls_sender(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _save_rahim(client)
    monkeypatch.setattr(chat_service, "send_whatsapp_message", lambda *args: (_ for _ in ()).throw(AssertionError()))
    response = client.post("/api/chat/message", json={"message": "whatsapp e Rahim ke bolo ami pore call korbo"})
    assert response.json()["intent"] == "whatsapp_draft"


@pytest.mark.parametrize(
    ("contact_name", "message", "expected"),
    [
        ("Rahim", "WhatsApp e Rahim ke message pathao: ami kal ashbo.", "ami kal ashbo."),
        ("রহিম", "রহিমকে হোয়াটসঅ্যাপে মেসেজ পাঠাও: আমি কাল আসব।", "আমি কাল আসব।"),
    ],
)
def test_banglish_and_bangla_send_forms_are_explicit(tmp_path, monkeypatch, contact_name, message, expected) -> None:
    client = _client(tmp_path, monkeypatch)
    _enable_send(monkeypatch)
    contact_store.save_contact(contact_name, "01712345678")
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        chat_service,
        "send_whatsapp_message",
        lambda request_id, phone, text: (calls.append((phone, text)) or WhatsAppSendResult("submitted", "Submitted.")),
    )
    response = client.post("/api/chat/message", json={"message": message})
    assert response.json()["intent"] == "whatsapp_send"
    assert calls == [("8801712345678", expected)]


def test_negated_and_quoted_send_never_call_sender(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _enable_send(monkeypatch)
    _save_rahim(client)
    calls: list[object] = []
    monkeypatch.setattr(chat_service, "send_whatsapp_message", lambda *args: calls.append(args))
    for message in (
        "Don't send a WhatsApp message to Rahim saying hello.",
        '"Send a WhatsApp message to Rahim saying hello."',
    ):
        client.post("/api/chat/message", json={"message": message})
    assert calls == []


def test_fuzzy_only_match_cannot_auto_send(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _enable_send(monkeypatch)
    _save_rahim(client)
    monkeypatch.setattr(chat_service, "send_whatsapp_message", lambda *args: (_ for _ in ()).throw(AssertionError()))
    response = client.post(
        "/api/chat/message",
        json={"message": "Send a WhatsApp message to Rohim saying hello."},
    )
    data = response.json()
    assert data["intent"] == "whatsapp_send"
    assert data["status"] == "needs_more_info"
    assert data["pending_task"] is None


def test_login_required_does_not_leave_pending_send(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _enable_send(monkeypatch)
    _save_rahim(client)
    monkeypatch.setattr(chat_service, "send_whatsapp_message", lambda *args: WhatsAppSendResult("login_required", "Login required."))
    response = client.post(
        "/api/chat/message",
        json={"message": "Send a WhatsApp message to Rahim saying hello."},
    )
    data = response.json()
    assert data["status"] == "login_required"
    assert data["pending_task"] is None


def test_sender_ledger_blocks_duplicate_request(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(whatsapp_sender, "LEDGER_FILE", tmp_path / "ledger.json")
    monkeypatch.setattr(whatsapp_sender, "_build_driver", lambda: (_ for _ in ()).throw(RuntimeError("browser unavailable")))
    first = whatsapp_sender.send_whatsapp_message("same-turn", "8801712345678", "hello")
    second = whatsapp_sender.send_whatsapp_message("same-turn", "8801712345678", "hello")
    assert first.status == "unknown"
    assert second.status == "unknown"
    ledger = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert ledger["same-turn"]["status"] == "unknown"


def test_mocked_browser_sends_once_after_recipient_verification(monkeypatch) -> None:
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    class Element:
        def __init__(self, text: str = "") -> None:
            self.text = text
            self.clicks = 0

        def is_displayed(self) -> bool:
            return True

        def click(self) -> None:
            self.clicks += 1

        def send_keys(self, *values) -> None:
            self.text = "".join(value for value in values if isinstance(value, str))

    composer = Element()
    send = Element()
    body = Element("8801712345678")
    conversation = Element()

    class Driver:
        def get(self, url: str) -> None:
            assert "phone=8801712345678" in url

        def find_element(self, by, selector):
            if by == By.TAG_NAME:
                return body
            if "conversation-panel-body" in selector:
                return conversation
            if "conversation-compose-box-input" in selector:
                return composer
            if "data-testid='send'" in selector:
                return send
            if "data-testid='chat-list'" in selector:
                return conversation
            raise NoSuchElementException(selector)

    result = whatsapp_sender._send_once(Driver(), "8801712345678", "hello")
    assert result.status == "submitted"
    assert send.clicks == 1
    assert composer.text == "hello"