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
    draft_id = provider.create_draft(PreparedEmail(("to@example.com",), (), (), "S", "B"))
    created = client.post("/api/gmail/draft-approvals", json={"draft_id": draft_id, "to": ["to@example.com"], "subject": "S", "body": "B"})
    approval_id = created.json()["approval"]["approval_id"]
    assert "draft_fingerprint" not in created.text
    approved = client.post(f"/api/gmail/draft-approvals/{approval_id}/approve")
    assert approved.json()["status"] == "approved"
    assert "draft_fingerprint" not in approved.text
    assert provider.sent_messages == ()


def test_approval_status_apis_exclude_internal_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: agent)
    client = TestClient(app)
    draft_id = provider.create_draft(PreparedEmail(("to@example.com",), (), (), "S", "B"))
    created = client.post(
        "/api/gmail/draft-approvals",
        json={"draft_id": draft_id, "to": ["to@example.com"], "subject": "S", "body": "B"},
    )
    approval_id = created.json()["approval"]["approval_id"]
    assert "draft_fingerprint" not in client.get(f"/api/gmail/draft-approvals/{approval_id}").text
    cancelled = client.post(f"/api/gmail/draft-approvals/{approval_id}/cancel")
    assert cancelled.json()["status"] == "cancelled"
    assert "draft_fingerprint" not in cancelled.text


def test_invalidation_still_works_without_exposing_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: agent)
    client = TestClient(app)
    draft_id = provider.create_draft(PreparedEmail(("to@example.com",), (), (), "S", "B"))
    approval = agent.request_draft_approval(draft_id, PreparedEmail(("to@example.com",), (), (), "S", "B"))
    provider._drafts[draft_id] = PreparedEmail(("to@example.com",), (), (), "Changed", "B")
    response = client.post(f"/api/gmail/draft-approvals/{approval.approval_id}/approve")
    assert response.json()["status"] == "invalidated"
    assert "draft_fingerprint" not in response.text


def test_gmail_draft_execution_includes_sanitized_pending_approval() -> None:
    provider = MockGmailProvider()
    result = GmailAgent(provider).execute(
        "draft",
        to=("to@example.com",),
        subject="Subject",
        body="Body",
        open_browser=False,
    )
    approval = result.metadata["approval"]
    assert result.approval_id == approval["approval_id"]
    assert approval["status"] == "pending"
    assert approval["body"] == "Body"
    assert "draft_fingerprint" not in repr(approval)
    assert "local_path" not in repr(approval)
    assert "content_sha256" not in repr(approval)
    assert provider.sent_messages == ()


def _draft_approval(provider: MockGmailProvider, email: PreparedEmail) -> tuple[GmailAgent, str, str]:
    agent = GmailAgent(provider)
    draft_id = provider.create_draft(email)
    approval = agent.request_draft_approval(draft_id, email)
    return agent, draft_id, approval.approval_id


@pytest.mark.parametrize("field", ["subject", "body", "to", "cc", "bcc"])
def test_changed_draft_fields_invalidate_before_approval(field: str) -> None:
    provider = MockGmailProvider()
    original = _email()
    agent, draft_id, approval_id = _draft_approval(provider, original)
    changed = {
        "subject": "Changed subject",
        "body": "Changed body",
        "to": ("other@example.com",),
        "cc": ("cc@example.com",),
        "bcc": ("bcc@example.com",),
    }
    provider._drafts[draft_id] = _email(**{field: changed[field]})
    result = agent.approve_draft(approval_id)
    assert result.status == "invalidated"


def test_active_account_change_invalidates_approval() -> None:
    provider = MockGmailProvider()
    provider.active_account = lambda: {"account_id": "account-a"}
    agent, draft_id, approval_id = _draft_approval(provider, _email())
    provider.active_account = lambda: {"account_id": "account-b"}
    result = agent.approve_draft(approval_id)
    assert result.status == "invalidated"
    assert result.draft_id == draft_id


def test_attachment_added_removed_filename_and_content_changes_invalidate(tmp_path: Path) -> None:
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_bytes(b"one")
    second_path.write_bytes(b"two")
    attachment = GmailAttachment("first.txt", "text/plain", 3, "attachment-1", str(first_path))
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email(attachments=(attachment,)))

    provider._drafts[draft_id] = _email(attachments=())
    assert agent.get_draft_approval(approval_id).status == "invalidated"

    for current_attachment in (
        (GmailAttachment("first.txt", "text/plain", 3, "attachment-1", str(first_path)), GmailAttachment("extra.txt", "text/plain", 3, "attachment-2", str(second_path))),
        (GmailAttachment("renamed.txt", "text/plain", 3, "attachment-1", str(first_path)),),
        (GmailAttachment("first.txt", "application/octet-stream", 3, "attachment-1", str(first_path)),),
    ):
        provider = MockGmailProvider()
        agent, draft_id, approval_id = _draft_approval(provider, _email(attachments=(attachment,)))
        provider._drafts[draft_id] = _email(attachments=current_attachment)
        assert agent.get_draft_approval(approval_id).status == "invalidated"

    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email(attachments=(attachment,)))
    first_path.write_bytes(b"new")
    provider._drafts[draft_id] = _email(attachments=(attachment,))
    assert agent.get_draft_approval(approval_id).status == "invalidated"


def test_approved_draft_edit_invalidates_on_status_inspection() -> None:
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email())
    assert agent.approve_draft(approval_id).status == "approved"
    provider._drafts[draft_id] = _email(body="Edited after approval")
    assert agent.get_draft_approval(approval_id).status == "invalidated"


def test_missing_draft_invalidates_safely() -> None:
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email())
    del provider._drafts[draft_id]
    result = agent.approve_draft(approval_id)
    assert result.status == "invalidated"


def test_terminal_states_are_safe_and_revalidation_is_idempotent() -> None:
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email())
    provider._drafts[draft_id] = _email(subject="Changed")
    first = agent.get_draft_approval(approval_id)
    second = agent.get_draft_approval(approval_id)
    assert first.status == second.status == "invalidated"
    with pytest.raises(PermissionError):
        agent.approve_draft(approval_id)

    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email())
    assert agent.cancel_draft(approval_id).status == "cancelled"
    provider._drafts[draft_id] = _email(subject="Changed")
    assert agent.get_draft_approval(approval_id).status == "cancelled"


def test_crlf_and_lf_have_the_same_fingerprint() -> None:
    provider = MockGmailProvider()
    actual = _email(body="Meet at 10 AM\r\nTomorrow")
    agent, draft_id, approval_id = _draft_approval(provider, actual)
    provider._drafts[draft_id] = _email(body="Meet at 10 AM\nTomorrow")
    assert agent.get_draft_approval(approval_id).status == "pending"
    assert agent.approve_draft(approval_id).status == "approved"


def test_revalidation_api_excludes_raw_attachment_metadata_and_secrets() -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: agent)
    try:
        draft_id = provider.create_draft(_email())
        created = TestClient(app).post(
            "/api/gmail/draft-approvals",
            json={"draft_id": draft_id, "to": ["to@example.com"], "subject": "Subject", "body": "Body"},
        )
        approval_id = created.json()["approval"]["approval_id"]
        response = TestClient(app).get(f"/api/gmail/draft-approvals/{approval_id}")
        text = response.text
        assert "content_sha256" not in text
        assert "local_path" not in text
        assert "access_token" not in text
        assert "refresh_token" not in text
        assert "MIME" not in text
    finally:
        monkeypatch.undo()


def test_revalidation_never_calls_send() -> None:
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _draft_approval(provider, _email())
    provider._drafts[draft_id] = _email(body="Changed")
    assert agent.get_draft_approval(approval_id).status == "invalidated"
    assert provider.sent_messages == ()