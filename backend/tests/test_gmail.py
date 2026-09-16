from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.agents.gmail_agent import GmailAgent, format_agent_result
from app.agents import gmail_agent as gmail_agent_module
from app.chat import service as chat_service
from app.main import app
from app.providers.gmail_provider import email_preview, normalize_google_message
from app.providers.mock_gmail_provider import MockGmailProvider
from app.schemas.gmail import GmailActionResult, GmailEmail, GmailThread, PreparedEmail
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


def test_legacy_approve_and_send_is_permanently_blocked(monkeypatch) -> None:
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
    assert rejected.error == "legacy_send_path_disabled"
    blocked = agent.approve_and_send(pending.approval_id)
    assert blocked.status == "blocked"
    assert len(provider.sent_messages) == 0


def test_legacy_approve_and_send_never_calls_send_prepared(monkeypatch) -> None:
    provider = MockGmailProvider()
    agent = GmailAgent(provider)
    send_prepared = Mock(wraps=provider.send_prepared)
    monkeypatch.setattr(provider, "send_prepared", send_prepared)

    result = agent.approve_and_send("historical-approval")

    assert result.error == "legacy_send_path_disabled"
    send_prepared.assert_not_called()


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


def test_gmail_chat_routing_and_api(monkeypatch) -> None:
    monkeypatch.setenv("NEXA_GMAIL_PROVIDER", "mock")
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


def test_gmail_connect_returns_pending_without_exposing_oauth_data(monkeypatch) -> None:
    class _PendingProvider:
        def begin_authorization(self):
            return {"provider": "google", "state": "authorization_pending"}

    class _Agent:
        provider = _PendingProvider()

    monkeypatch.setattr("app.api.routes.gmail.get_gmail_agent", lambda: _Agent())
    response = TestClient(app).post("/api/gmail/accounts/connect", json={"open_browser": True})

    assert response.status_code == 200
    assert response.json() == {
        "status": "pending",
        "action": "authorize",
        "message": "Gmail authorization started in the default browser.",
        "metadata": {"provider": "google", "state": "authorization_pending"},
    }
    assert "authorization_url" not in response.text
    assert "access_token" not in response.text
    assert "refresh_token" not in response.text


class _RecordingGmailAgent:
    def __init__(self) -> None:
        self.provider = MockGmailProvider()
        self.calls: list[tuple[str, dict]] = []
        self.emails = tuple(
            GmailEmail(f"real-message-{index}", f"real-thread-{index}", "sender@example.com", (), (), f"Security {index}", "", "", "")
            for index in range(1, 6)
        )
        self.email = self.emails[0]

    def execute(self, action: str, **kwargs):
        self.calls.append((action, kwargs))
        if action in {"unread", "search"}:
            return GmailActionResult("completed", action, "Found 5 email(s).", emails=self.emails)
        if action == "read":
            return GmailActionResult("completed", action, "Email loaded.", emails=(self.email,))
        if action == "thread":
            return GmailActionResult("completed", action, "Loaded 1 message.", thread=GmailThread(kwargs["thread_id"], (self.email,)))
        return GmailActionResult("completed", action, "Done.")


def test_gmail_chat_builds_real_queries_and_ids(monkeypatch) -> None:
    agent = _RecordingGmailAgent()
    monkeypatch.setattr(chat_service, "get_gmail_agent", lambda: agent)

    chat_service._gmail_chat_response("Show my latest 5 unread emails", None)
    assert agent.calls[0] == ("unread", {"limit": 5})
    assert "message_id" not in agent.calls[0][1]
    assert "thread_id" not in agent.calls[0][1]

    agent.calls.clear()
    chat_service._gmail_chat_response("Search my emails from Google", None)
    assert agent.calls[0] == ("search", {"limit": 20, "query": "from:google"})

    agent.calls.clear()
    chat_service._gmail_chat_response("Show emails with subject security", None)
    assert agent.calls[0] == ("search", {"limit": 20, "query": "subject:security"})

    agent.calls.clear()
    chat_service._gmail_chat_response("Read my latest email from Google", None)
    assert agent.calls[0] == ("search", {"limit": 20, "query": "from:google"})
    assert agent.calls[1] == ("read", {"message_id": "real-message-1", "full": True})

    agent.calls.clear()
    chat_service._gmail_chat_response("Open the latest unread email", None)
    assert agent.calls[0] == ("unread", {"limit": 20})
    assert agent.calls[1] == ("read", {"message_id": "real-message-1", "full": True})

    agent.calls.clear()
    chat_service._gmail_chat_response("Show the full thread of the latest email", None)
    assert agent.calls[0] == ("search", {"limit": 20, "query": ""})
    assert agent.calls[1] == ("thread", {"thread_id": "real-thread-1", "full": True})


def test_gmail_chat_unread_latest_is_a_list_and_renders_all_results(monkeypatch) -> None:
    agent = _RecordingGmailAgent()
    monkeypatch.setattr(chat_service, "get_gmail_agent", lambda: agent)

    response = chat_service._gmail_chat_response("Show my latest 5 unread emails", None)

    assert agent.calls == [("unread", {"limit": 5})]
    assert "msg-supervisor" not in response.answer
    assert "msg-invoice" not in response.answer
    for index in range(1, 6):
        assert f"Security {index}" in response.answer

    agent.calls.clear()
    chat_service._gmail_chat_response("Show my latest unread emails", None)
    assert agent.calls == [("unread", {"limit": 20})]


def test_gmail_chat_provider_display_is_dynamic(monkeypatch) -> None:
    agent = _RecordingGmailAgent()
    monkeypatch.setattr(chat_service, "get_gmail_agent", lambda: agent)
    response = chat_service._gmail_chat_response("Show my unread emails", None)
    assert response.provider == "MockGmailProvider"


def test_cached_agent_switches_explicit_provider_without_losing_approvals(monkeypatch) -> None:
    monkeypatch.setenv("NEXA_GMAIL_PROVIDER", "mock")
    mock_agent = gmail_agent_module.get_gmail_agent()
    approvals = mock_agent.approvals
    monkeypatch.setenv("NEXA_GMAIL_PROVIDER", "google")
    google_agent = gmail_agent_module.get_gmail_agent()
    assert google_agent.provider.__class__.__name__ == "GoogleGmailProvider"
    assert google_agent.approvals is approvals
