from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.agents.gmail_agent import GmailAgent, format_agent_result
from app.main import app
from app.providers.gmail_provider import email_preview, normalize_google_message
from app.providers.mock_gmail_provider import MockGmailProvider
from app.schemas.gmail import PreparedEmail
from app.security import gmail_approvals


def test_provider_interface_and_mock_search() -> None:
    provider = MockGmailProvider()
    assert [email.id for email in provider.search_emails("project")] == ["msg-supervisor"]
    assert [email.id for email in provider.list_unread()] == ["msg-supervisor"]
    assert [email.id for email in provider.search_by_sender("accounts@example.com")] == ["msg-invoice"]
    assert [email.id for email in provider.search_by_subject("Invoice")] == ["msg-invoice"]
    assert [email.id for email in provider.search_by_date(after="2026/09/10")] == [
        "msg-supervisor",
        "msg-invoice",
        "msg-injection",
    ]


def test_mock_read_thread_attachments_labels_and_archive(tmp_path: Path) -> None:
    provider = MockGmailProvider()
    email = provider.get_email("msg-invoice")
    assert email.subject == "September Invoice"
    assert provider.get_thread("thread-report").messages[0].id == "msg-supervisor"
    assert provider.list_attachment_metadata("msg-invoice")[0].filename == "invoice.pdf"
    downloaded = provider.download_attachment("msg-invoice", "att-invoice", tmp_path)
    assert downloaded.read_bytes() == b"Mock invoice content"
    provider.add_labels("msg-invoice", ["STARRED"])
    assert "STARRED" in provider.get_email("msg-invoice").labels
    assert "INBOX" not in provider.archive_email("msg-invoice").labels


def test_mock_draft_reply_and_reply_all() -> None:
    provider = MockGmailProvider()
    assert provider.create_draft(PreparedEmail(("a@example.com",), (), (), "Subject", "Body")) == "draft-1"
    assert provider.create_reply_draft("thread-report", "Thanks") == "draft-2"
    assert provider.create_reply_all_draft("thread-report", "Thanks", user_email="student@example.com") == "draft-3"


def test_secure_preview_marks_email_as_untrusted() -> None:
    email = MockGmailProvider().get_email("msg-injection")
    preview = email_preview(email)
    assert preview["untrusted_content"] is True
    assert "ignore previous instructions" in preview["security_flags"]
    assert "attacker@example.com" in preview["snippet"]


def test_prompt_injection_is_context_only_and_does_not_send() -> None:
    agent = GmailAgent(MockGmailProvider())
    result = agent.execute("summarize", message_id="msg-injection")
    assert result.status == "completed"
    assert "untrusted" in result.metadata["summary"].lower()
    blocked = agent.execute("send", to=("attacker@example.com",), subject="x", body="y")
    assert blocked.status == "blocked"
    assert not agent.provider.sent_messages


def test_no_approval_blocks_and_explicit_approval_sends(monkeypatch) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    monkeypatch.setattr("app.agents.gmail_agent.is_permission_enabled", lambda key: True)
    pending = agent.execute(
        "prepare_send",
        to=("recipient@example.com",),
        subject="Hello",
        body="Approved body",
    )
    assert pending.status == "pending_confirmation"
    assert pending.approval_id
    assert not provider.sent_messages
    rejected = agent.approve_and_send("missing-approval")
    assert rejected.status == "blocked"
    sent = agent.approve_and_send(pending.approval_id)
    assert sent.status == "executed"
    assert len(provider.sent_messages) == 1


def test_approval_controller_rejects_unapproved_request() -> None:
    controller = gmail_approvals.EmailApprovalController()
    prepared = PreparedEmail(("recipient@example.com",), (), (), "Hello", "Body")
    pending = controller.create_pending(prepared, GmailAgent(MockGmailProvider())._outgoing_preview(prepared))
    try:
        controller.approve(pending.approval_id, approved_by_user=False)
    except PermissionError:
        pass
    else:
        raise AssertionError("unapproved email was accepted")


def test_google_message_normalization_does_not_return_html_as_raw_preview() -> None:
    message = {
        "id": "m1",
        "threadId": "t1",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Hello"},
            ],
            "mimeType": "text/html",
            "body": {"data": "PGJvZHk+SGk8c2NyaXB0PmFsZXJ0KDEpPC9zY3JpcHQ+PC9ib2R5Pg=="},
        },
    }
    normalized = normalize_google_message(message)
    preview = email_preview(normalized)
    assert "<script>" not in preview["snippet"]
    assert preview["snippet"] == "Hi"


def test_gmail_chat_routing_and_api() -> None:
    client = TestClient(app)
    route = client.post("/api/chat/message", json={"message": "Show my unread emails"})
    assert route.status_code == 200
    assert route.json()["intent"] == "gmail_skill"
    assert route.json()["route_debug"] is None
    command = client.post("/api/gmail/command", json={"action": "unread"})
    assert command.status_code == 200
    assert command.json()["status"] == "completed"
    direct = client.post("/api/gmail/command", json={"action": "send", "to": ["a@example.com"], "subject": "x", "body": "y"})
    assert direct.json()["status"] == "blocked"


def test_gmail_permission_disabled_blocks(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.gmail.is_permission_enabled", lambda key: False)
    client = TestClient(app)
    response = client.post("/api/gmail/command", json={"action": "unread"})
    assert response.json()["status"] == "blocked"
