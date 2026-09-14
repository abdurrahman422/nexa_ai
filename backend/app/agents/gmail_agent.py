"""NEXA-owned Gmail agent and untrusted email boundary."""

from __future__ import annotations

from dataclasses import asdict
import os
from typing import Any

from app.audit.event_log import record_audit_event
from app.permissions import is_permission_enabled, permission_denied_message
from app.providers.gmail_provider import GmailProvider, GmailProviderError, email_preview, prompt_injection_flags, safe_text
from app.providers.mock_gmail_provider import MockGmailProvider
from app.providers.google_gmail_provider import GoogleGmailProvider
from app.schemas.gmail import GmailActionResult, GmailPreview, PreparedEmail
from app.security.gmail_approvals import EmailApprovalController


class GmailAgent:
    """Accept structured Gmail actions and never expose provider credentials."""

    def __init__(self, provider: GmailProvider | None = None, approvals: EmailApprovalController | None = None) -> None:
        self.provider = provider or MockGmailProvider()
        self.approvals = approvals or EmailApprovalController()

    def execute(self, action: str, **kwargs: Any) -> GmailActionResult:
        if not is_permission_enabled("gmail_skill"):
            return GmailActionResult("blocked", action, permission_denied_message("gmail_skill"), error="permission_disabled")
        try:
            if action == "auth_status":
                raw_status = getattr(self.provider, "auth_status", lambda: {"provider": "mock", "authenticated": True, "state": "offline"})()
                status = {
                    key: raw_status[key]
                    for key in ("provider", "authenticated", "state", "scope")
                    if key in raw_status
                }
                return GmailActionResult("completed", action, "Gmail authentication status loaded.", metadata=status)
            if action == "authorize":
                authorize = getattr(self.provider, "start_authorization", None)
                if authorize is None:
                    return GmailActionResult("completed", action, "Mock Gmail provider does not require OAuth.", metadata={"provider": "mock", "authenticated": True, "state": "offline"})
                return GmailActionResult("completed", action, "Gmail authorization completed.", metadata=self._public_auth_status(authorize(open_browser=bool(kwargs.get("open_browser", True)))))
            if action == "search":
                emails = tuple(self.provider.search_emails(str(kwargs.get("query", "")), int(kwargs.get("limit", 20))))
                return GmailActionResult("completed", action, f"Found {len(emails)} email(s).", emails=emails)
            if action == "unread":
                emails = tuple(self.provider.list_unread(int(kwargs.get("limit", 20))))
                return GmailActionResult("completed", action, f"Found {len(emails)} unread email(s).", emails=emails)
            if action == "sender":
                emails = tuple(self.provider.search_by_sender(str(kwargs["sender"]), int(kwargs.get("limit", 20))))
                return GmailActionResult("completed", action, f"Found {len(emails)} email(s).", emails=emails)
            if action == "subject":
                emails = tuple(self.provider.search_by_subject(str(kwargs["subject"]), int(kwargs.get("limit", 20))))
                return GmailActionResult("completed", action, f"Found {len(emails)} email(s).", emails=emails)
            if action == "date":
                emails = tuple(self.provider.search_by_date(kwargs.get("after"), kwargs.get("before"), int(kwargs.get("limit", 20))))
                return GmailActionResult("completed", action, f"Found {len(emails)} email(s).", emails=emails)
            if action in {"read", "summarize"}:
                email = self.provider.get_email(str(kwargs["message_id"]), include_body=bool(kwargs.get("full", action == "summarize")))
                preview = self._preview(email)
                metadata = {"summary": self._summary(email) if action == "summarize" else None}
                return GmailActionResult("completed", action, "Email loaded.", emails=(email,), preview=preview, metadata=metadata)
            if action == "thread":
                thread = self.provider.get_thread(str(kwargs["thread_id"]), include_body=bool(kwargs.get("full", False)))
                return GmailActionResult("completed", action, f"Loaded {len(thread.messages)} message(s).", thread=thread)
            if action == "attachments":
                attachments = tuple(self.provider.list_attachment_metadata(str(kwargs["message_id"])))
                return GmailActionResult("completed", action, f"Found {len(attachments)} attachment(s).", metadata={"attachments": [asdict(item) for item in attachments]})
            if action == "download_attachment":
                path = self.provider.download_attachment(str(kwargs["message_id"]), str(kwargs["attachment_id"]), kwargs.get("output_dir", "attachments"))
                return GmailActionResult("completed", action, "Attachment downloaded.", attachment_path=str(path))
            if action == "labels":
                labels = tuple(self.provider.list_labels())
                return GmailActionResult("completed", action, f"Found {len(labels)} label(s).", labels=labels)
            if action == "add_labels":
                email = self.provider.add_labels(str(kwargs["message_id"]), kwargs.get("label_ids", ()))
                return GmailActionResult("completed", action, "Labels added.", emails=(email,))
            if action == "remove_labels":
                email = self.provider.remove_labels(str(kwargs["message_id"]), kwargs.get("label_ids", ()))
                return GmailActionResult("completed", action, "Labels removed.", emails=(email,))
            if action == "archive":
                email = self.provider.archive_email(str(kwargs["message_id"]))
                return GmailActionResult("completed", action, "Email archived.", emails=(email,))
            if action in {"draft", "reply_draft", "reply_all_draft"}:
                draft_id = self._create_draft(action, kwargs)
                return GmailActionResult("completed", action, "Draft created.", draft_id=draft_id)
            if action == "prepare_send":
                return self._prepare_send(kwargs)
            if action == "send":
                return GmailActionResult("blocked", action, "Direct AI-controlled sending is blocked. Prepare a preview and obtain user approval.", error="direct_send_blocked")
            return GmailActionResult("blocked", action, "Unknown Gmail action.", error="unknown_action")
        except (KeyError, ValueError, GmailProviderError, PermissionError) as exc:
            return GmailActionResult("failed", action, str(exc), error=str(exc))

    def approve_and_send(self, approval_id: str) -> GmailActionResult:
        if not is_permission_enabled("email_control"):
            return GmailActionResult("blocked", "send", permission_denied_message("email_control"), error="permission_disabled")
        try:
            pending = self.approvals.approve(approval_id, approved_by_user=True)
            message_id = self.provider.send_prepared(pending.email)
            record_audit_event("gmail", "email_send", "executed", "high", ",".join(pending.email.to), "Approved email sent.")
            return GmailActionResult("executed", "send", "Approved email sent.", metadata={"message_id": message_id})
        except (PermissionError, GmailProviderError) as exc:
            record_audit_event("gmail", "email_send", "blocked", "high", "", str(exc))
            return GmailActionResult("blocked", "send", str(exc), error=str(exc))

    def _create_draft(self, action: str, kwargs: dict[str, Any]) -> str:
        body = str(kwargs.get("body", ""))
        if action == "reply_draft":
            return self.provider.create_reply_draft(str(kwargs["thread_id"]), body, attachments=kwargs.get("attachments", ()))
        if action == "reply_all_draft":
            return self.provider.create_reply_all_draft(str(kwargs["thread_id"]), body, user_email=kwargs.get("user_email", "student@example.com"), attachments=kwargs.get("attachments", ()))
        return self.provider.create_draft(self._prepared_from_kwargs(kwargs))

    def _prepare_send(self, kwargs: dict[str, Any]) -> GmailActionResult:
        if not is_permission_enabled("email_control"):
            return GmailActionResult("blocked", "prepare_send", permission_denied_message("email_control"), error="permission_disabled")
        prepared = self.provider.prepare_email(self._prepared_from_kwargs(kwargs))
        preview = self._outgoing_preview(prepared)
        pending = self.approvals.create_pending(prepared, preview)
        record_audit_event("gmail", "email_send", "pending_confirmation", "high", ",".join(prepared.to), "Email preview created; not sent.")
        return GmailActionResult("pending_confirmation", "prepare_send", "Email preview created. Explicit user approval is required before sending.", preview=preview, approval_id=pending.approval_id)

    @staticmethod
    def _prepared_from_kwargs(kwargs: dict[str, Any]) -> PreparedEmail:
        return PreparedEmail(
            to=tuple(kwargs.get("to", ())),
            cc=tuple(kwargs.get("cc", ())),
            bcc=tuple(kwargs.get("bcc", ())),
            subject=str(kwargs.get("subject", "")),
            body=str(kwargs.get("body", "")),
            attachments=tuple(kwargs.get("attachments", ())),
            thread_id=kwargs.get("thread_id"),
            in_reply_to=kwargs.get("in_reply_to"),
            references=tuple(kwargs.get("references", ())),
        )

    def _preview(self, email: Any) -> GmailPreview:
        data = email_preview(email)
        return GmailPreview(
            sender=data["sender"], recipients=tuple(data["recipients"]), subject=data["subject"], date=data["date"], snippet=data["snippet"], labels=tuple(data["labels"]), attachments=tuple(email.attachments), security_flags=tuple(data["security_flags"]),
        )

    @staticmethod
    def _outgoing_preview(email: PreparedEmail) -> GmailPreview:
        return GmailPreview("NEXA user", email.to, email.subject, "", safe_text(email.body, 320), (), email.attachments, False, ())

    @staticmethod
    def _summary(email: Any) -> str:
        flags = prompt_injection_flags(email.body_text)
        if flags:
            return "Email facts are available, but instruction-like content was treated as untrusted data."
        return safe_text(email.body_text, 500) or email.snippet

    @staticmethod
    def _public_auth_status(status: dict[str, Any]) -> dict[str, Any]:
        return {
            key: status[key]
            for key in ("provider", "authenticated", "state", "scope")
            if key in status
        }


def format_agent_result(result: GmailActionResult) -> dict[str, Any]:
    data = asdict(result)
    data["emails"] = [asdict(email) for email in result.emails]
    for email in data["emails"]:
        email["body_text"] = safe_text(email.get("body_text", ""))
    if result.thread:
        data["thread"] = {"id": result.thread.id, "messages": [asdict(email) for email in result.thread.messages]}
        for email in data["thread"]["messages"]:
            email["body_text"] = safe_text(email.get("body_text", ""))
    if result.preview:
        data["preview"] = asdict(result.preview)
    return data


def build_gmail_provider() -> GmailProvider:
    """Build the explicitly selected provider; mock remains the default."""
    provider_name = os.getenv("NEXA_GMAIL_PROVIDER", "mock").strip().lower()
    if provider_name == "mock":
        return MockGmailProvider()
    if provider_name == "google":
        return GoogleGmailProvider()
    raise ValueError("NEXA_GMAIL_PROVIDER must be 'mock' or 'google'.")


_DEFAULT_AGENT: GmailAgent | None = None
_DEFAULT_PROVIDER_CONFIG: tuple[str, str, str] | None = None
_DEFAULT_APPROVALS = EmailApprovalController()


def _provider_config() -> tuple[str, str, str]:
    return (
        os.getenv("NEXA_GMAIL_PROVIDER", "mock").strip().lower(),
        os.getenv("NEXA_GMAIL_CREDENTIALS_PATH", ""),
        os.getenv("NEXA_GMAIL_TOKEN_PATH", ""),
    )


def get_gmail_agent() -> GmailAgent:
    global _DEFAULT_AGENT, _DEFAULT_PROVIDER_CONFIG
    config = _provider_config()
    if _DEFAULT_AGENT is None:
        _DEFAULT_AGENT = GmailAgent(build_gmail_provider(), approvals=_DEFAULT_APPROVALS)
        _DEFAULT_PROVIDER_CONFIG = config
    elif config != _DEFAULT_PROVIDER_CONFIG:
        _DEFAULT_AGENT.provider = build_gmail_provider()
        _DEFAULT_PROVIDER_CONFIG = config
    return _DEFAULT_AGENT
