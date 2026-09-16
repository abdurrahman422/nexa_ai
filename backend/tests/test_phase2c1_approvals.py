from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agents.gmail_agent import GmailAgent
from app.main import app
from app.providers.mock_gmail_provider import MockGmailProvider
from app.schemas.gmail import GmailAttachment, PreparedEmail
from app.security.gmail_approvals import GmailApprovalController


def _email(**changes: object) -> PreparedEmail:
    values: dict[str, object] = {
        "to": ("to@example.com",), "cc": (), "bcc": (), "subject": "Subject",
        "body": "Body", "attachments": (),
    }
    values.update(changes)
    return PreparedEmail(**values)


def test_draft_approval_starts_pending_and_ids_are_unpredictable() -> None:
    controller = GmailApprovalController()
    first = controller.create_approval("draft-1", "account-1", _email())
    second = controller.create_approval("draft-1", "account-1", _email())
    assert first.status == "pending"
    assert first.approval_id != second.approval_id
    assert len(first.approval_id) >= 32


def test_approval_transitions_and_repeated_approval_fail_safely() -> None:
    controller = GmailApprovalController()
    approval = controller.create_approval("draft-1", "account-1", _email())
    assert controller.approve(approval.approval_id).status == "approved"
    with pytest.raises(PermissionError):
        controller.approve(approval.approval_id)

    cancelled = controller.create_approval("draft-2", "account-1", _email())
    controller.cancel(cancelled.approval_id)
    with pytest.raises(PermissionError):
        controller.approve(cancelled.approval_id)

    invalidated = controller.create_approval("draft-3", "account-1", _email())
    controller.invalidate(invalidated.approval_id)
    with pytest.raises(PermissionError):
        controller.approve(invalidated.approval_id)


def test_expired_approval_cannot_be_approved() -> None:
    controller = GmailApprovalController(ttl_seconds=1)
    approval = controller.create_approval("draft-1", "account-1", _email())
    expired = type(approval)(**{**approval.__dict__, "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()})
    controller._approvals[approval.approval_id] = expired
    with pytest.raises(PermissionError):
        controller.approve(approval.approval_id)
    assert controller.get_approval(approval.approval_id).status == "expired"


@pytest.mark.parametrize("change", [
    {"to": ("other@example.com",)},
    {"subject": "Other"},
    {"body": "Other body"},
    {"attachments": (GmailAttachment("a.txt", "text/plain", 1, "a", safe_status="safe"),)},
])
def test_draft_changes_produce_different_fingerprints(change: dict[str, object]) -> None:
    controller = GmailApprovalController()
    first = controller.create_approval("draft-1", "account-1", _email())
    second = controller.create_approval("draft-1", "account-1", _email(**change))
    assert first.draft_fingerprint != second.draft_fingerprint


def test_attachment_content_change_produces_different_fingerprint(tmp_path: Path) -> None:
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_bytes(b"one")
    second_path.write_bytes(b"two")
    controller = GmailApprovalController()
    first = controller.create_approval("draft-1", "account-1", _email(attachments=(GmailAttachment("a.txt", "text/plain", 3, "a", str(first_path)),)))
    second = controller.create_approval("draft-1", "account-1", _email(attachments=(GmailAttachment("a.txt", "text/plain", 3, "a", str(second_path)),)))
    assert first.draft_fingerprint != second.draft_fingerprint


def test_active_account_change_produces_different_fingerprint() -> None:
    controller = GmailApprovalController()
    first = controller.create_approval("draft-1", "account-1", _email())
    second = controller.create_approval("draft-1", "account-2", _email())
    assert first.draft_fingerprint != second.draft_fingerprint


def test_approval_data_excludes_oauth_secrets() -> None:
    approval = GmailApprovalController().create_approval("draft-1", "account-1", _email(body="client_secret refresh_token access_token"))
    rendered = repr(approval)
    assert "client_secret" not in rendered
    assert "refresh_token" not in rendered
    assert "access_token" not in rendered
    assert "Body" not in rendered


def test_draft_approval_api_never_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: agent)
    client = TestClient(app)
    created = client.post("/api/gmail/draft-approvals", json={"draft_id": "draft-1", "to": ["to@example.com"], "subject": "S", "body": "B"})
    approval_id = created.json()["approval"]["approval_id"]
    approved = client.post(f"/api/gmail/draft-approvals/{approval_id}/approve")
    assert approved.json()["status"] == "approved"
    assert provider.sent_messages == ()