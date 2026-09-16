from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.agents.gmail_agent import GmailAgent
from app.main import app
from app.providers.gmail_provider import GmailProviderError
from app.providers.mock_gmail_provider import MockGmailProvider
from app.schemas.gmail import GmailAttachment, PreparedEmail


def _email(**changes: object) -> PreparedEmail:
    values: dict[str, object] = {
        "to": ("to@example.com",),
        "cc": (),
        "bcc": (),
        "subject": "Subject",
        "body": "Body with secret message content",
        "attachments": (),
    }
    values.update(changes)
    return PreparedEmail(**values)


def _capture_audit(monkeypatch: pytest.MonkeyPatch) -> list[tuple[object, ...]]:
    events: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        "app.agents.gmail_agent.record_audit_event",
        lambda *args: events.append(args),
    )
    return events


def _approved(
    provider: MockGmailProvider,
    email: PreparedEmail | None = None,
) -> tuple[GmailAgent, str, str]:
    email = email or _email()
    agent = GmailAgent(provider)
    draft_id = provider.create_draft(email)
    approval = agent.request_draft_approval(draft_id, email)
    agent.approve_draft(approval.approval_id)
    return agent, draft_id, approval.approval_id


def _event_names(events: list[tuple[object, ...]]) -> list[str]:
    return [str(event[1]) for event in events]


def test_approval_creation_and_approval_are_audited_without_content(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _capture_audit(monkeypatch)
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    email = _email(body="DO NOT LOG THIS BODY")
    draft_id = provider.create_draft(email)

    approval = agent.request_draft_approval(draft_id, email)
    agent.approve_draft(approval.approval_id)

    assert _event_names(events) == ["approval_created", "approval_approved"]
    serialized = repr(events)
    assert "DO NOT LOG THIS BODY" not in serialized
    assert "draft_fingerprint" not in serialized
    assert "content_sha256" not in serialized
    assert "local_path" not in serialized
    assert "attachment bytes" not in serialized
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "client_secret" not in serialized


def test_cancel_and_expiration_are_audited(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _capture_audit(monkeypatch)
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    draft_id = provider.create_draft(_email())
    cancelled = agent.request_draft_approval(draft_id, _email())
    agent.cancel_draft(cancelled.approval_id)

    expired = agent.request_draft_approval(draft_id, _email())
    current = agent.draft_approvals.get_approval(expired.approval_id)
    assert current is not None
    agent.draft_approvals._approvals[expired.approval_id] = type(current)(
        **{
            **current.__dict__,
            "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        }
    )
    assert agent.get_draft_approval(expired.approval_id).status == "expired"

    assert "approval_cancelled" in _event_names(events)
    assert "approval_expired" in _event_names(events)


@pytest.mark.parametrize("failure", ["stale", "account", "missing"])
def test_invalidation_reasons_are_audited(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    events = _capture_audit(monkeypatch)
    provider = MockGmailProvider()
    if failure == "account":
        provider.active_account = lambda: {"account_id": "account-a"}
    agent, draft_id, approval_id = _approved(provider)

    if failure == "stale":
        provider._drafts[draft_id] = _email(subject="Changed")
        result, _ = agent.send_approved_draft(approval_id)
    elif failure == "account":
        provider.active_account = lambda: {"account_id": "account-b"}
        result, _ = agent.send_approved_draft(approval_id)
    else:
        del provider._drafts[draft_id]
        result, _ = agent.send_approved_draft(approval_id)

    assert result.status == "invalidated"
    names = _event_names(events)
    assert "approval_invalidated" in names
    expected_event = {
        "stale": "draft_changed",
        "account": "account_mismatch",
        "missing": "draft_missing",
    }[failure]
    assert expected_event in names
    expected_reason = "draft_unavailable" if failure == "missing" else expected_event
    assert any(f"reason={expected_reason}" in str(event[5]) for event in events)


def test_send_claim_success_duplicate_and_blocked_events_are_audited(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _capture_audit(monkeypatch)
    provider = MockGmailProvider()
    agent, _, approval_id = _approved(provider)

    sent, _ = agent.send_approved_draft(approval_id)
    repeated, _ = agent.send_approved_draft(approval_id)

    assert sent.status == "sent"
    assert repeated.status == "sent"
    names = _event_names(events)
    assert "send_claimed" in names
    assert "send_succeeded" in names
    assert "duplicate_send" in names


def test_provider_failure_is_audited_and_api_error_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _capture_audit(monkeypatch)
    provider = MockGmailProvider()
    agent, _, approval_id = _approved(provider)
    monkeypatch.setattr(
        provider,
        "send_draft",
        Mock(side_effect=GmailProviderError("raw Google payload access_token=secret")),
    )

    with pytest.raises(GmailProviderError) as error:
        agent.send_approved_draft(approval_id)
    assert str(error.value) == (
        "Gmail send failed or the send result could not be confirmed. "
        "Check Gmail Sent before attempting any further action."
    )
    assert "raw Google" not in str(error.value)
    assert "provider_send_failure" in _event_names(events)
    assert "send_blocked" in _event_names(events)

    api_provider = MockGmailProvider()
    api_agent, _, api_approval_id = _approved(api_provider)
    monkeypatch.setattr(
        api_provider,
        "send_draft",
        Mock(side_effect=GmailProviderError("raw Google payload access_token=secret")),
    )
    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: api_agent)
    response = TestClient(app).post(f"/api/gmail/draft-approvals/{api_approval_id}/send")
    assert response.json()["error"] == str(error.value)
    assert "access_token" not in response.text
    assert "raw Google" not in response.text


def test_direct_chat_send_and_legacy_send_remain_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    monkeypatch.setattr("app.agents.gmail_agent.is_permission_enabled", lambda _: True)

    direct = agent.execute("send", to=("to@example.com",), subject="S", body="B")
    legacy = agent.approve_and_send("legacy-id")

    assert direct.status == "blocked"
    assert direct.error == "direct_send_blocked"
    assert legacy.status == "blocked"
    assert legacy.error == "legacy_send_path_disabled"
    assert provider.sent_messages == ()


def test_prepare_send_audit_uses_counts_without_recipient_or_content(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _capture_audit(monkeypatch)
    monkeypatch.setattr("app.agents.gmail_agent.is_permission_enabled", lambda _: True)
    agent = GmailAgent(MockGmailProvider())

    result = agent.execute(
        "prepare_send",
        to=("private-recipient@example.com",),
        subject="Private subject",
        body="Private body that must not be audited",
    )

    assert result.status == "pending_confirmation"
    assert len(events) == 1
    event = repr(events[0])
    assert events[0][1:3] == ("email_send", "pending_confirmation")
    assert "recipient_count=1" in event
    assert "attachment_count=0" in event
    assert "private-recipient@example.com" not in event
    assert "Private subject" not in event
    assert "Private body that must not be audited" not in event