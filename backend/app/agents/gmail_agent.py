"""NEXA-owned Gmail agent and untrusted email boundary."""

from __future__ import annotations

from dataclasses import asdict
import os
import re
import webbrowser
from typing import Any

from app.audit.event_log import record_audit_event
from app.permissions import is_permission_enabled, permission_denied_message
from app.providers.gmail_provider import GmailProvider, GmailProviderError, email_preview, prompt_injection_flags, safe_text
from app.providers.mock_gmail_provider import MockGmailProvider
from app.providers.google_gmail_provider import GoogleGmailProvider
from app.schemas.gmail import GmailActionResult, GmailPreview, PreparedEmail
from app.security.gmail_approvals import EmailApprovalController, GmailApproval, GmailApprovalController

GMAIL_DRAFTS_URL = "https://mail.google.com/mail/u/0/#drafts"
_GMAIL_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class GmailAgent:
    """Accept structured Gmail actions and never expose provider credentials."""

    def __init__(self, provider: GmailProvider | None = None, approvals: EmailApprovalController | None = None, draft_approvals: GmailApprovalController | None = None) -> None:
        self.provider = provider or MockGmailProvider()
        self.approvals = approvals or EmailApprovalController()
        self.draft_approvals = draft_approvals or GmailApprovalController()

    def request_draft_approval(
        self,
        draft_id: str,
        email: PreparedEmail,
        attachment_metadata: tuple[dict[str, Any], ...] = (),
    ) -> GmailApproval:
        return self.draft_approvals.create_approval(
            draft_id,
            self._active_account_id(),
            email,
            attachment_metadata=attachment_metadata or None,
        )

    def get_draft_approval(self, approval_id: str) -> GmailApproval | None:
        approval = self.draft_approvals.get_approval(approval_id)
        if approval is None or approval.status in {"cancelled", "expired", "invalidated", "sending", "sent"}:
            return approval
        return self._revalidate_draft_approval(approval)

    def approve_draft(self, approval_id: str) -> GmailApproval:
        approval = self.draft_approvals.get_approval(approval_id)
        if approval is None:
            raise PermissionError("Approval was not found.")
        if approval.status in {"cancelled", "expired", "invalidated"}:
            raise PermissionError(f"Approval cannot be approved from status '{approval.status}'.")
        revalidated = self._revalidate_draft_approval(approval)
        if revalidated.status != "pending":
            return revalidated
        return self.draft_approvals.approve(approval_id)

    def cancel_draft(self, approval_id: str) -> GmailApproval:
        return self.draft_approvals.cancel(approval_id)

    def send_approved_draft(self, approval_id: str) -> tuple[GmailApproval, str | None]:
        if not is_permission_enabled("email_control"):
            raise PermissionError(permission_denied_message("email_control"))
        approval = self.draft_approvals.get_approval(approval_id)
        if approval is None:
            raise PermissionError("Approval was not found.")
        if approval.status != "approved":
            return approval, None

        # Gmail has no conditional compare-and-send transaction for drafts.send.
        # Keep this final read immediately before the local claim; Gmail web UI
        # edits can still occur in the tiny interval before the provider call.
        revalidated = self._revalidate_draft_approval(approval)
        if revalidated.status != "approved":
            return revalidated, None
        claimed = self.draft_approvals.claim_for_send(approval_id)
        if claimed.status != "sending":
            return claimed, None
        try:
            message_id = self.provider.send_draft(claimed.draft_id)
        except GmailProviderError as exc:
            self.draft_approvals.invalidate(approval_id)
            record_audit_event("gmail", "draft_send", "blocked", "high", "", str(exc))
            raise
        sent = self.draft_approvals.mark_sent(approval_id)
        record_audit_event("gmail", "draft_send", "executed", "high", ",".join(sent.to), "Approved Gmail draft sent.")
        return sent, message_id

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
            if action in {"draft", "reply_draft", "reply_all_draft", "forward_draft"}:
                draft_id = self._create_draft(action, kwargs)
                metadata = dict(getattr(self.provider, "last_draft_metadata", {}))
                metadata.setdefault("draft_id", draft_id)
                prepared = self._approval_email(kwargs, metadata)
                attachment_metadata: tuple[dict[str, Any], ...] = ()
                try:
                    snapshot = self.provider.get_draft_snapshot(draft_id)
                except GmailProviderError:
                    snapshot = None
                if snapshot is not None:
                    prepared = snapshot.email
                    attachment_metadata = snapshot.attachment_metadata
                approval = self.request_draft_approval(draft_id, prepared, attachment_metadata)
                metadata["approval_id"] = approval.approval_id
                metadata["approval"] = self._approval_preview(approval, prepared)
                metadata["operation"] = action
                if kwargs.get("draft_tone"):
                    metadata["tone"] = str(kwargs["draft_tone"])
                if kwargs.get("draft_styles"):
                    metadata["styles"] = list(kwargs["draft_styles"])
                metadata["browser_opened"] = False
                metadata["browser_url"] = GMAIL_DRAFTS_URL
                metadata["navigation"] = "drafts_fallback"
                metadata["navigation_identifier_used"] = None
                metadata["navigation_strategy"] = "drafts_fallback"
                if bool(kwargs.get("open_browser", True)):
                    exact_url = self._exact_draft_url(metadata) if action not in {"reply_draft", "reply_all_draft"} and metadata.get("body_present") is True else None
                    if exact_url:
                        try:
                            metadata["browser_opened"] = bool(webbrowser.open(exact_url))
                        except Exception:
                            metadata["browser_opened"] = False
                        if metadata["browser_opened"]:
                            metadata["browser_url"] = exact_url
                            metadata["navigation"] = "exact_draft"
                            metadata["navigation_identifier_used"] = metadata.get("message_id")
                            metadata["navigation_strategy"] = "message_id_draft_route"
                    if not metadata["browser_opened"]:
                        try:
                            metadata["browser_opened"] = bool(webbrowser.open(GMAIL_DRAFTS_URL))
                        except Exception:
                            metadata["browser_opened"] = False
                return GmailActionResult("completed", action, "Draft created. Review it in Gmail before sending.", draft_id=draft_id, approval_id=approval.approval_id, metadata=metadata)
            if action == "prepare_send":
                return self._prepare_send(kwargs)
            if action == "send":
                return GmailActionResult("blocked", action, "Direct AI-controlled sending is blocked. Prepare a preview and obtain user approval.", error="direct_send_blocked")
            return GmailActionResult("blocked", action, "Unknown Gmail action.", error="unknown_action")
        except (KeyError, ValueError, GmailProviderError, PermissionError) as exc:
            return GmailActionResult("failed", action, str(exc), error=str(exc))

    def approve_and_send(self, approval_id: str) -> GmailActionResult:
        return GmailActionResult(
            "blocked",
            "send",
            "Legacy prepared-email sending is disabled; send only through the controlled approved-draft flow.",
            error="legacy_send_path_disabled",
        )

    def _create_draft(self, action: str, kwargs: dict[str, Any]) -> str:
        body = str(kwargs.get("body", ""))
        if action == "reply_draft":
            return self.provider.create_reply_draft(str(kwargs["thread_id"]), body, attachments=kwargs.get("attachments", ()))
        if action == "reply_all_draft":
            user_email = kwargs.get("user_email")
            if not user_email:
                account = self.provider.active_account() if hasattr(self.provider, "active_account") else None
                user_email = account.get("email", "") if account else ""
            return self.provider.create_reply_all_draft(str(kwargs["thread_id"]), body, user_email=user_email, attachments=kwargs.get("attachments", ()))
        if action == "forward_draft":
            return self.provider.create_forward_draft(str(kwargs["message_id"]), kwargs.get("to", ()), body, attachments=kwargs.get("attachments", ()))
        return self.provider.create_draft(self._prepared_from_kwargs(kwargs))

    def _approval_email(self, kwargs: dict[str, Any], metadata: dict[str, Any]) -> PreparedEmail:
        return PreparedEmail(
            to=tuple(metadata.get("to") or kwargs.get("to", ())),
            cc=tuple(metadata.get("cc") or kwargs.get("cc", ())),
            bcc=tuple(metadata.get("bcc") or kwargs.get("bcc", ())),
            subject=str(metadata.get("subject") or kwargs.get("subject", "")),
            body=str(kwargs.get("body", "")),
            attachments=tuple(kwargs.get("attachments", ())),
            thread_id=metadata.get("thread_id") or kwargs.get("thread_id"),
        )

    def _active_account_id(self) -> str:
        active_account = self.provider.active_account() if hasattr(self.provider, "active_account") else None
        return str((active_account or {}).get("account_id", "mock"))

    def _revalidate_draft_approval(self, approval: GmailApproval) -> GmailApproval:
        try:
            snapshot = self.provider.get_draft_snapshot(approval.draft_id)
        except GmailProviderError:
            snapshot = None
        return self.draft_approvals.revalidate_approval(
            approval.approval_id,
            active_account_id=self._active_account_id(),
            draft_id=approval.draft_id,
            email=snapshot.email if snapshot is not None else None,
            attachment_metadata=snapshot.attachment_metadata if snapshot is not None else (),
        )

    @staticmethod
    def _approval_preview(approval: GmailApproval, email: PreparedEmail) -> dict[str, Any]:
        return {
            "approval_id": approval.approval_id,
            "draft_id": approval.draft_id,
            "active_account_id": approval.active_account_id,
            "to": list(approval.to),
            "cc": list(approval.cc),
            "bcc": list(approval.bcc),
            "subject": approval.subject,
            "body": email.body,
            "attachment_metadata": [
                {
                    "file_name": item.get("filename", ""),
                    "mime_type": item.get("mime_type", ""),
                    "size_bytes": item.get("size", 0),
                }
                for item in approval.attachment_metadata
            ],
            "created_at": approval.created_at,
            "expires_at": approval.expires_at,
            "status": approval.status,
        }

    @staticmethod
    def _exact_draft_url(metadata: dict[str, Any]) -> str | None:
        message_id = metadata.get("message_id")
        if isinstance(message_id, str) and _GMAIL_ID_RE.fullmatch(message_id):
            return f"https://mail.google.com/mail/u/0/#drafts/{message_id}"
        return None

    @staticmethod
    def _exact_thread_url(metadata: dict[str, Any]) -> str | None:
        thread_id = metadata.get("thread_id")
        if isinstance(thread_id, str) and _GMAIL_ID_RE.fullmatch(thread_id):
            return f"https://mail.google.com/mail/u/0/#all/{thread_id}"
        return None

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
