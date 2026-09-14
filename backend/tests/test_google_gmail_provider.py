from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
from google.oauth2.credentials import Credentials

from app.agents.gmail_agent import GmailAgent, build_gmail_provider
from app.gmail_accounts import GmailAccountStore
from app.providers.gmail_provider import GmailProviderError, email_preview
from app.providers.google_gmail_provider import GMAIL_READONLY_SCOPE, GoogleGmailProvider
from app.providers.mock_gmail_provider import MockGmailProvider


def _encoded(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode()


def _message(message_id: str = "m1") -> dict:
    return {
        "id": message_id,
        "threadId": "t1",
        "snippet": "Please review this message.",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "Supervisor <supervisor@example.com>"},
                {"name": "To", "value": "user@example.com"},
                {"name": "Subject", "value": "Project Report"},
                {"name": "Date", "value": "Mon, 14 Sep 2026 10:00:00 +0000"},
                {"name": "Message-ID", "value": "<m1@example.com>"},
            ],
            "mimeType": "multipart/mixed",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": _encoded("Please review this message.")}},
                {
                    "filename": "report.pdf",
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "a1", "size": 4},
                },
            ],
        },
    }


def _service() -> Mock:
    service = Mock()
    service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "m1"}],
    }
    service.users.return_value.messages.return_value.get.return_value.execute.return_value = _message()
    service.users.return_value.threads.return_value.get.return_value.execute.return_value = {
        "id": "t1",
        "messages": [_message("m1"), _message("m2")],
    }
    service.users.return_value.messages.return_value.attachments.return_value.get.return_value.execute.return_value = {
        "data": _encoded("test"),
    }
    service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [{"id": "INBOX", "name": "INBOX"}],
    }
    return service


def test_google_provider_uses_readonly_scope_and_normalizes_mocked_api() -> None:
    provider = GoogleGmailProvider(
        credentials_path="C:/outside/credentials.json",
        token_path="C:/outside/token.json",
        service=_service(),
    )
    assert provider.auth_status()["scope"] == GMAIL_READONLY_SCOPE
    email = provider.get_email("m1")
    assert email.sender == "Supervisor <supervisor@example.com>"
    assert email.subject == "Project Report"
    assert email.attachments[0].filename == "report.pdf"
    preview = email_preview(email)
    assert preview["untrusted_content"] is True
    assert "<script>" not in preview["snippet"]


def test_google_provider_search_thread_labels_and_attachment_download(tmp_path: Path) -> None:
    service = _service()
    provider = GoogleGmailProvider(service=service, max_attachment_bytes=100)
    assert [item.id for item in provider.search_emails("is:unread", limit=5)] == ["m1"]
    assert len(provider.get_thread("t1").messages) == 2
    assert provider.list_labels() == [{"id": "INBOX", "name": "INBOX"}]
    destination = provider.download_attachment("m1", "a1", tmp_path)
    assert destination.read_bytes() == b"test"
    assert destination.parent == tmp_path.resolve()


def test_google_provider_rejects_all_phase_2a_write_operations() -> None:
    provider = GoogleGmailProvider(service=_service())
    with pytest.raises(GmailProviderError, match="disabled in Phase 2A"):
        provider.archive_email("m1")
    with pytest.raises(GmailProviderError, match="draft creation is disabled"):
        provider.create_draft(Mock())
    with pytest.raises(GmailProviderError, match="sending is disabled"):
        provider.send_prepared(Mock())


def test_provider_selection_defaults_to_mock_and_supports_google(monkeypatch) -> None:
    monkeypatch.delenv("NEXA_GMAIL_PROVIDER", raising=False)
    assert isinstance(build_gmail_provider(), MockGmailProvider)
    monkeypatch.setenv("NEXA_GMAIL_PROVIDER", "google")
    assert isinstance(build_gmail_provider(), GoogleGmailProvider)


def test_unknown_provider_selection_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("NEXA_GMAIL_PROVIDER", "other")
    with pytest.raises(ValueError, match="mock.*google"):
        build_gmail_provider()


def test_agent_auth_status_does_not_expose_credentials(monkeypatch) -> None:
    monkeypatch.setattr("app.agents.gmail_agent.is_permission_enabled", lambda key: True)
    agent = GmailAgent(GoogleGmailProvider(service=_service()))
    result = agent.execute("auth_status")
    assert result.status == "completed"
    assert "token_path" not in result.metadata
    assert "credentials_path" not in result.metadata


def test_google_provider_auth_status_reports_configuration_without_loading_token_contents(tmp_path: Path) -> None:
    provider = GoogleGmailProvider(
        credentials_path=tmp_path / "client.json",
        token_path=tmp_path / "token.json",
        service=_service(),
    )
    status = provider.auth_status()
    assert status["state"] == "authorization_required"
    assert status["scope"] == GMAIL_READONLY_SCOPE
    assert "access_token" not in status
    assert "refresh_token" not in status


def test_two_accounts_have_isolated_token_paths_and_registry_has_no_secrets(tmp_path: Path) -> None:
    store = GmailAccountStore(tmp_path / "gmail")
    first = store.register("first@example.com")
    second = store.register("second@example.com")
    assert first["account_id"] != second["account_id"]
    assert first["token_path"] != second["token_path"]
    registry = json.loads((tmp_path / "gmail" / "accounts.json").read_text(encoding="utf-8"))
    serialized = json.dumps(registry)
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "token" in serialized


def test_switching_active_account_changes_provider_token_source(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "gmail"
    monkeypatch.setenv("NEXA_GMAIL_ROOT", str(root))
    store = GmailAccountStore(root)
    first = store.register("first@example.com")
    first_path = store.token_path(first["account_id"])
    first_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("{}", encoding="utf-8")
    second = store.register("second@example.com")
    second_path = store.token_path(second["account_id"])
    second_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.write_text("{}", encoding="utf-8")
    provider = GoogleGmailProvider(service=_service())

    provider.switch_account(first["account_id"])
    assert provider.token_path == first_path
    provider.switch_account(second["account_id"])
    assert provider.token_path == second_path


def test_disconnect_account_does_not_affect_another_account(tmp_path: Path) -> None:
    store = GmailAccountStore(tmp_path / "gmail")
    first = store.register("first@example.com")
    second = store.register("second@example.com")
    first_path = store.token_path(first["account_id"])
    second_path = store.token_path(second["account_id"])
    first_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("first", encoding="utf-8")
    second_path.write_text("second", encoding="utf-8")

    store.disconnect(first["account_id"])

    assert not first_path.exists()
    assert second_path.read_text(encoding="utf-8") == "second"
    assert [item["account_id"] for item in store.list_accounts()] == [second["account_id"]]


def test_missing_active_account_never_falls_back_to_another_account(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "gmail"
    monkeypatch.setenv("NEXA_GMAIL_ROOT", str(root))
    store = GmailAccountStore(root)
    first = store.register("first@example.com")
    second = store.register("second@example.com")
    for account in (first, second):
        token_path = store.token_path(account["account_id"])
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text("{}", encoding="utf-8")
    store.disconnect(second["account_id"])
    provider = GoogleGmailProvider(credentials_path=tmp_path / "credentials.json")

    with pytest.raises(GmailProviderError, match="authorization is required"):
        provider.get_email("another-account-message")
    assert [item["account_id"] for item in store.list_accounts()] == [first["account_id"]]


def test_missing_active_account_requires_oauth(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXA_GMAIL_ROOT", str(tmp_path / "gmail"))
    provider = GoogleGmailProvider(credentials_path=tmp_path / "credentials.json", service=None)
    with pytest.raises(GmailProviderError, match="authorization is required"):
        provider.get_email("real-message")


def test_legacy_single_token_migrates_once_to_isolated_account(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "gmail"
    legacy = root / "token.json"
    legacy.parent.mkdir(parents=True)
    credentials = Credentials(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=list((GMAIL_READONLY_SCOPE,)),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    legacy.write_text(credentials.to_json(), encoding="utf-8")
    monkeypatch.setenv("NEXA_GMAIL_ROOT", str(root))
    monkeypatch.setenv("NEXA_GMAIL_TOKEN_PATH", str(legacy))
    provider = GoogleGmailProvider(credentials_path=tmp_path / "credentials.json")
    monkeypatch.setattr(provider, "_profile_email", lambda value: "migrated@example.com")

    status = provider.auth_status()

    assert status["account_id"] == GmailAccountStore.account_id_for_email("migrated@example.com")
    assert not legacy.exists()
    assert provider.token_path == root / "accounts" / status["account_id"] / "token.json"
    assert provider.token_path.exists()
    assert len(GmailAccountStore(root).list_accounts()) == 1
