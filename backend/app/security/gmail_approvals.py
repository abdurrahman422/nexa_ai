"""One-time, content-bound approval controller for Gmail sends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from threading import Lock

from app.schemas.gmail import GmailPreview, PreparedEmail


@dataclass(frozen=True)
class PendingEmailAction:
    approval_id: str
    content_hash: str
    preview: GmailPreview
    email: PreparedEmail
    expires_at: str


class EmailApprovalController:
    """Stores pending send requests separately from the GmailAgent.

    The agent can create a pending request, but has no agent method that marks
    it approved. Approval is a separate host/controller operation.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._pending: dict[str, PendingEmailAction] = {}
        self._lock = Lock()

    @staticmethod
    def content_hash(email: PreparedEmail) -> str:
        canonical = "\n".join(
            [
                ",".join(email.to),
                ",".join(email.cc),
                ",".join(email.bcc),
                email.subject,
                email.body,
                email.thread_id or "",
                email.in_reply_to or "",
                " ".join(email.references),
                "|".join(f"{item.filename}:{item.size}:{item.attachment_id}" for item in email.attachments),
            ]
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def create_pending(self, email: PreparedEmail, preview: GmailPreview) -> PendingEmailAction:
        now = datetime.now(timezone.utc)
        pending = PendingEmailAction(
            approval_id=token_urlsafe(24),
            content_hash=self.content_hash(email),
            preview=preview,
            email=email,
            expires_at=(now + timedelta(seconds=self.ttl_seconds)).isoformat(),
        )
        with self._lock:
            self._pending[pending.approval_id] = pending
        return pending

    def get_pending(self, approval_id: str) -> PendingEmailAction | None:
        with self._lock:
            pending = self._pending.get(approval_id)
            if pending is None:
                return None
            if datetime.now(timezone.utc) >= datetime.fromisoformat(pending.expires_at):
                self._pending.pop(approval_id, None)
                return None
            return pending

    def approve(self, approval_id: str, *, approved_by_user: bool) -> PendingEmailAction:
        if not approved_by_user:
            raise PermissionError("Explicit user approval is required.")
        pending = self.get_pending(approval_id)
        if pending is None:
            raise PermissionError("Approval is missing, expired, or already used.")
        with self._lock:
            self._pending.pop(approval_id, None)
        return pending
