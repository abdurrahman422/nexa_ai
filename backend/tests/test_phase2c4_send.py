from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.agents.gmail_agent import GmailAgent
from app.main import app
from app.providers.gmail_provider import GmailProviderError
from app.providers.google_gmail_provider import GoogleGmailProvider
from app.providers.mock_gmail_provider import MockGmailProvider
from app.schemas.gmail import GmailAttachment, PreparedEmail


def _email(**changes: object) -> PreparedEmail:
    values: dict[str, object] = {
        "to": ("to@example.com",),
        "cc": (),
        "bcc": (),
        "subject": "Subject",
        "body": "Body",
        "attachments": (),
    }
    values.update(changes)
    return PreparedEmail(**values)


def _approval(provider: MockGmailProvider, email: PreparedEmail | None = None) -> tuple[GmailAgent, str, str]:
    email = email or _email()
    agent = GmailAgent(provider)
    draft_id = provider.create_draft(email)
    approval = agent.request_draft_approval(draft_id, email)
    assert agent.approve_draft(approval.approval_id).status == "approved"
    return agent, draft_id, approval.approval_id


def test_approved_unchanged_draft_sends_once_and_becomes_sent() -> None:
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _approval(provider)

    sent, message_id = agent.send_approved_draft(approval_id)

    assert sent.status == "sent"
    assert message_id == "message-1"
    assert provider.send_draft_call_count == 1
    assert provider.sent_draft_ids == [draft_id]
    assert agent.get_draft_approval(approval_id).status == "sent"
    sent_again, message_again = agent.send_approved_draft(approval_id)
    assert sent_again.status == "sent"
    assert message_again is None
    assert provider.send_draft_call_count == 1


def test_approval_flow_requires_explicit_approval_before_send() -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    draft_id = provider.create_draft(_email())
    approval = agent.request_draft_approval(draft_id, _email())

    result, message_id = agent.send_approved_draft(approval.approval_id)
    assert result.status == "pending"
    assert message_id is None
    assert provider.send_draft_call_count == 0

    approved = agent.approve_draft(approval.approval_id)
    assert approved.status == "approved"

    sent, message_id = agent.send_approved_draft(approval.approval_id)
    assert sent.status == "sent"
    assert message_id == "message-1"
    assert provider.send_draft_call_count == 1


@pytest.mark.parametrize("status", ["pending", "cancelled", "expired", "invalidated"])
def test_non_approved_states_cannot_send(status: str) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    draft_id = provider.create_draft(_email())
    approval = agent.request_draft_approval(draft_id, _email())
    if status == "cancelled":
        approval = agent.cancel_draft(approval.approval_id)
    elif status == "invalidated":
        approval = agent.draft_approvals.invalidate(approval.approval_id)
    elif status == "expired":
        approval = type(approval)(**{**approval.__dict__, "expires_at": "2000-01-01T00:00:00+00:00"})
        agent.draft_approvals._approvals[approval.approval_id] = approval
        approval = agent.draft_approvals.get_approval(approval.approval_id)

    result, message_id = agent.send_approved_draft(approval.approval_id)
    assert result.status == status
    assert message_id is None
    assert provider.send_draft_call_count == 0


@pytest.mark.parametrize("field", ["subject", "body", "to", "cc", "bcc"])
def test_changed_draft_field_invalidates_at_final_revalidation(field: str) -> None:
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _approval(provider)
    changed = {
        "subject": "Changed subject",
        "body": "Changed body",
        "to": ("other@example.com",),
        "cc": ("cc@example.com",),
        "bcc": ("bcc@example.com",),
    }
    provider._drafts[draft_id] = _email(**{field: changed[field]})

    result, message_id = agent.send_approved_draft(approval_id)

    assert result.status == "invalidated"
    assert message_id is None
    assert provider.send_draft_call_count == 0


def test_attachment_changes_and_missing_draft_invalidate(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    first.write_bytes(b"one")
    attachment = GmailAttachment("first.txt", "text/plain", 3, "attachment-1", str(first))
    provider = MockGmailProvider()
    agent, draft_id, approval_id = _approval(provider, _email(attachments=(attachment,)))
    first.write_bytes(b"two")

    result, message_id = agent.send_approved_draft(approval_id)
    assert result.status == "invalidated"
    assert message_id is None
    assert provider.send_draft_call_count == 0

    provider = MockGmailProvider()
    agent, draft_id, approval_id = _approval(provider)
    del provider._drafts[draft_id]
    result, message_id = agent.send_approved_draft(approval_id)
    assert result.status == "invalidated"
    assert message_id is None
    assert provider.send_draft_call_count == 0


def test_account_switch_invalidates_without_sending() -> None:
    provider = MockGmailProvider()
    provider.active_account = lambda: {"account_id": "account-a"}
    agent, _, approval_id = _approval(provider)
    provider.active_account = lambda: {"account_id": "account-b"}

    result, message_id = agent.send_approved_draft(approval_id)

    assert result.status == "invalidated"
    assert message_id is None
    assert provider.send_draft_call_count == 0


def test_concurrent_send_requests_claim_once() -> None:
    provider = MockGmailProvider()
    agent, _, approval_id = _approval(provider)
    barrier = Barrier(2)

    def send() -> tuple[str, str | None]:
        barrier.wait()
        result, message_id = agent.send_approved_draft(approval_id)
        return result.status, message_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: send(), range(2)))

    assert provider.send_draft_call_count == 1
    assert all(status in {"sending", "sent"} for status, _ in results)
    assert any(status == "sent" for status, _ in results)


def test_provider_failure_does_not_mark_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent, _, approval_id = _approval(provider)
    monkeypatch.setattr(provider, "send_draft", Mock(side_effect=GmailProviderError("send failed")))

    with pytest.raises(GmailProviderError, match="send failed"):
        agent.send_approved_draft(approval_id)

    assert agent.get_draft_approval(approval_id).status == "invalidated"


def test_provider_failure_cannot_be_retried_automatically(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent, _, approval_id = _approval(provider)
    send_draft = Mock(side_effect=GmailProviderError("ambiguous send"))
    monkeypatch.setattr(provider, "send_draft", send_draft)

    with pytest.raises(GmailProviderError):
        agent.send_approved_draft(approval_id)
    result, message_id = agent.send_approved_draft(approval_id)

    assert result.status == "invalidated"
    assert message_id is None
    send_draft.assert_called_once()


def test_send_api_is_explicit_and_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MockGmailProvider()
    agent, _, approval_id = _approval(provider)
    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: agent)
    monkeypatch.setattr("app.agents.gmail_agent.is_permission_enabled", lambda _: True)

    response = TestClient(app).post(f"/api/gmail/draft-approvals/{approval_id}/send")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "sent"
    assert payload["approval"]["status"] == "sent"
    assert payload["message_id"] == "message-1"
    for secret in ("draft_fingerprint", "access_token", "refresh_token", "raw", "bytes"):
        assert secret not in response.text


def test_google_provider_calls_drafts_send_once(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Mock()
    service.users.return_value.drafts.return_value.send.return_value.execute.return_value = {"id": "message-42"}
    provider = GoogleGmailProvider(service=service)
    monkeypatch.setattr(provider, "_get_credentials", lambda **kwargs: object())

    assert provider.send_draft("draft-42") == "message-42"
    service.users.return_value.drafts.return_value.send.assert_called_once_with(
        userId="me", body={"id": "draft-42"}
    )


def test_google_provider_sanitizes_ambiguous_drafts_send_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Mock()
    service.users.return_value.drafts.return_value.send.return_value.execute.side_effect = RuntimeError(
        "secret token and raw request details"
    )
    provider = GoogleGmailProvider(service=service)
    monkeypatch.setattr(provider, "_get_credentials", lambda **kwargs: object())

    with pytest.raises(GmailProviderError) as error:
        provider.send_draft("draft-ambiguous")

    assert str(error.value) == (
        "Gmail send failed or the send result could not be confirmed. "
        "Check Gmail Sent before attempting any further action."
    )
    assert "secret token" not in str(error.value)
    service.users.return_value.drafts.return_value.send.assert_called_once()
