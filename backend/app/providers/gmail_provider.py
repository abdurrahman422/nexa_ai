"""Provider boundary for Gmail operations.

The agent depends on this interface, never on Google credentials or a raw
Google API service. Providers return normalized NEXA data structures.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import html
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from email.message import EmailMessage
from email.utils import getaddresses
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

from app.schemas.gmail import (
    GmailAttachment,
    GmailEmail,
    GmailDraftSnapshot,
    GmailThread,
    PreparedEmail,
)


class GmailProviderError(RuntimeError):
    """Expected provider failure that is safe to show to the user."""


class GmailProvider(ABC):
    """Stable Gmail capability boundary used by GmailAgent."""

    @abstractmethod
    def search_emails(self, query: str, limit: int = 20) -> list[GmailEmail]: ...

    @abstractmethod
    def get_email(self, message_id: str, include_body: bool = True) -> GmailEmail: ...

    @abstractmethod
    def get_thread(self, thread_id: str, include_body: bool = True) -> GmailThread: ...

    def list_unread(self, limit: int = 20) -> list[GmailEmail]:
        return self.search_emails("is:unread", limit)

    def search_by_sender(self, sender: str, limit: int = 20) -> list[GmailEmail]:
        return self.search_emails(f"from:{sender}", limit)

    def search_by_subject(self, subject: str, limit: int = 20) -> list[GmailEmail]:
        return self.search_emails(f"subject:{subject}", limit)

    def search_by_date(self, after: str | None = None, before: str | None = None, limit: int = 20) -> list[GmailEmail]:
        parts = []
        if after:
            parts.append(f"after:{after}")
        if before:
            parts.append(f"before:{before}")
        return self.search_emails(" ".join(parts), limit)

    @abstractmethod
    def list_attachment_metadata(self, message_id: str) -> list[GmailAttachment]: ...

    @abstractmethod
    def download_attachment(self, message_id: str, attachment_id: str, output_dir: str | Path) -> Path: ...

    @abstractmethod
    def list_labels(self) -> list[dict[str, str]]: ...

    @abstractmethod
    def add_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail: ...

    @abstractmethod
    def remove_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail: ...

    @abstractmethod
    def archive_email(self, message_id: str) -> GmailEmail: ...

    @abstractmethod
    def create_draft(self, prepared: PreparedEmail) -> str: ...

    def get_draft_snapshot(self, draft_id: str) -> GmailDraftSnapshot:
        raise GmailProviderError("Gmail draft revalidation is unavailable for this provider.")

    def create_reply_draft(self, thread_id: str, body: str, **kwargs: Any) -> str:
        thread = self.get_thread(thread_id)
        target = _reply_target(thread)
        return self.create_draft(
            _reply_message(target, body, to=(target.reply_to or target.sender,), **kwargs)
        )

    def create_reply_all_draft(self, thread_id: str, body: str, **kwargs: Any) -> str:
        thread = self.get_thread(thread_id)
        target = _reply_target(thread)
        current_user = str(kwargs.pop("user_email", "")).lower()
        recipients = _unique_addresses((target.reply_to or target.sender, *target.recipients, *target.cc))
        recipients = tuple(address for address in recipients if address.lower() != current_user)
        to = recipients[:1]
        cc = recipients[1:]
        return self.create_draft(_reply_message(target, body, to=to, cc=cc, **kwargs))

    def create_forward_draft(self, message_id: str, to: Iterable[str], body: str = "", **kwargs: Any) -> str:
        source = self.get_email(message_id, include_body=True)
        subject = source.subject if source.subject.lower().startswith("fwd:") else f"Fwd: {source.subject}"
        forwarded = (
            body.strip()
            + ("\n\n" if body.strip() else "")
            + "---------- Forwarded message ----------\n"
            + f"From: {source.sender}\n"
            + f"Date: {source.date}\n"
            + f"Subject: {source.subject}\n\n"
            + safe_text(source.body_text, 12000)
        )
        return self.create_draft(
            PreparedEmail(
                to=_unique_addresses(to),
                cc=_unique_addresses(kwargs.pop("cc", ())),
                bcc=_unique_addresses(kwargs.pop("bcc", ())),
                subject=subject,
                body=forwarded,
                attachments=tuple(kwargs.pop("attachments", ())),
            )
        )

    @abstractmethod
    def prepare_email(self, email: PreparedEmail) -> PreparedEmail: ...

    @abstractmethod
    def send_prepared(self, email: PreparedEmail) -> str: ...

    @abstractmethod
    def send_draft(self, draft_id: str) -> str: ...


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden = True
        if tag == "br" and not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden = False

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def safe_text(value: str, limit: int = 4000) -> str:
    parser = _VisibleTextParser()
    try:
        parser.feed(value or "")
        text = " ".join("".join(parser.parts).split())
    except Exception:
        text = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return text[:limit]


def prompt_injection_flags(value: str) -> tuple[str, ...]:
    normalized = (value or "").lower()
    markers = (
        "ignore previous instructions",
        "ignore all previous instructions",
        "system message",
        "developer message",
        "send my files",
        "reveal your prompt",
    )
    return tuple(marker for marker in markers if marker in normalized)


def email_preview(email: GmailEmail) -> dict[str, Any]:
    text = safe_text(email.body_text, 320)
    flags = prompt_injection_flags(text)
    return {
        "id": email.id,
        "thread_id": email.thread_id,
        "sender": email.sender,
        "recipients": list(email.recipients),
        "cc": list(email.cc),
        "subject": email.subject,
        "date": email.date,
        "snippet": text or email.snippet[:320],
        "labels": list(email.labels),
        "attachments": [attachment.__dict__ for attachment in email.attachments],
        "untrusted_content": True,
        "security_flags": list(flags),
    }


def _reply_target(thread: GmailThread) -> GmailEmail:
    if not thread.messages:
        raise GmailProviderError("The thread has no replyable messages.")
    excluded_labels = {"DRAFT", "SENT", "TRASH", "SPAM"}
    for message in reversed(thread.messages):
        if not excluded_labels.intersection(message.labels):
            return message
    raise GmailProviderError("No matching received email was found in the thread.")


def _unique_addresses(addresses: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for _, address in getaddresses([address for address in addresses if address]):
        normalized = address.strip()
        if normalized and normalized.lower() not in {item.lower() for item in result}:
            result.append(normalized)
    return tuple(result)


def _reply_message(target: GmailEmail, body: str, *, to: Iterable[str], cc: Iterable[str] = (), **kwargs: Any) -> PreparedEmail:
    subject = target.subject if target.subject.lower().startswith("re:") else f"Re: {target.subject}"
    return PreparedEmail(
        to=_unique_addresses(to),
        cc=_unique_addresses(cc),
        bcc=_unique_addresses(kwargs.pop("bcc", ())),
        subject=subject,
        body=body,
        attachments=tuple(kwargs.pop("attachments", ())),
        thread_id=target.thread_id,
        in_reply_to=target.message_id,
        references=target.references + ((target.message_id,) if target.message_id else ()),
    )


def _decode_data(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded)
    except (binascii.Error, ValueError) as exc:
        raise GmailProviderError("Gmail returned invalid encoded content.") from exc


def _header(headers: list[dict[str, str]], name: str) -> str:
    for item in headers:
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


def _addresses(value: str) -> tuple[str, ...]:
    return _unique_addresses((address for _, address in getaddresses([value])))


def _body_from_payload(payload: dict[str, Any]) -> str:
    if payload.get("body", {}).get("data"):
        return _decode_data(payload["body"]["data"]).decode("utf-8", errors="replace")
    parts = payload.get("parts", [])
    plain = ""
    html_body = ""
    for part in parts:
        candidate = _body_from_payload(part) if part.get("parts") else ""
        data = part.get("body", {}).get("data")
        decoded = _decode_data(data).decode("utf-8", errors="replace") if data else candidate
        if part.get("mimeType") == "text/plain" and not plain:
            plain = decoded
        elif part.get("mimeType") == "text/html" and not html_body:
            html_body = decoded
    return plain or html_body


def normalize_google_message(message: dict[str, Any], include_body: bool = True) -> GmailEmail:
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    body = _body_from_payload(payload) if include_body else ""
    attachments = tuple(_attachments_from_payload(payload))
    return GmailEmail(
        id=str(message.get("id", "")),
        thread_id=str(message.get("threadId", "")),
        sender=_header(headers, "From"),
        recipients=_addresses(_header(headers, "To")),
        cc=_addresses(_header(headers, "Cc")),
        subject=_header(headers, "Subject"),
        date=_header(headers, "Date"),
        snippet=str(message.get("snippet", "")),
        body_text=body,
        labels=tuple(message.get("labelIds", [])),
        attachments=attachments,
        reply_to=_header(headers, "Reply-To") or None,
        message_id=_header(headers, "Message-ID") or None,
        references=tuple(_header(headers, "References").split()),
    )


def _attachments_from_payload(payload: dict[str, Any]) -> list[GmailAttachment]:
    found: list[GmailAttachment] = []
    for part in payload.get("parts", []):
        filename = part.get("filename", "")
        body = part.get("body", {})
        if filename:
            found.append(GmailAttachment(filename, part.get("mimeType", "application/octet-stream"), int(body.get("size", 0) or 0), body.get("attachmentId", "")))
        found.extend(_attachments_from_payload(part))
    return found


class ExistingSkillGmailProvider(GmailProvider):
    """Adapter for the existing skill's Google API service.

    A service must be injected by the host. This prevents provider construction
    from silently starting OAuth and keeps credentials out of GmailAgent.
    """

    def __init__(self, service: Any | None = None, *, service_factory: Any | None = None, max_attachment_bytes: int = 10 * 1024 * 1024) -> None:
        self._service = service
        self._service_factory = service_factory
        self.max_attachment_bytes = max_attachment_bytes

    @property
    def service(self) -> Any:
        if self._service is None and self._service_factory is not None:
            self._service = self._service_factory()
        if self._service is None:
            raise GmailProviderError("A Gmail service is not configured for this provider.")
        return self._service

    def search_emails(self, query: str, limit: int = 20) -> list[GmailEmail]:
        response = self.service.users().messages().list(userId="me", q=query or None, maxResults=max(1, min(limit, 100))).execute()
        return [self.get_email(item["id"], include_body=False) for item in response.get("messages", [])]

    def get_email(self, message_id: str, include_body: bool = True) -> GmailEmail:
        message = self.service.users().messages().get(userId="me", id=message_id, format="full" if include_body else "metadata").execute()
        return normalize_google_message(message, include_body)

    def get_thread(self, thread_id: str, include_body: bool = True) -> GmailThread:
        thread = self.service.users().threads().get(userId="me", id=thread_id, format="full" if include_body else "metadata").execute()
        return GmailThread(str(thread.get("id", thread_id)), tuple(normalize_google_message(item, include_body) for item in thread.get("messages", [])))

    def list_attachment_metadata(self, message_id: str) -> list[GmailAttachment]:
        return list(self.get_email(message_id, include_body=True).attachments)

    def download_attachment(self, message_id: str, attachment_id: str, output_dir: str | Path) -> Path:
        attachments = {item.attachment_id: item for item in self.list_attachment_metadata(message_id)}
        item = attachments.get(attachment_id)
        if item is None:
            raise GmailProviderError("Attachment was not found in the requested message.")
        if item.size > self.max_attachment_bytes:
            raise GmailProviderError("Attachment exceeds the configured size limit.")
        response = self.service.users().messages().attachments().get(userId="me", messageId=message_id, id=attachment_id).execute()
        data = _decode_data(response.get("data", ""))
        if len(data) > self.max_attachment_bytes:
            raise GmailProviderError("Downloaded attachment exceeds the configured size limit.")
        directory = Path(output_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = Path(item.filename).name or f"attachment-{attachment_id}"
        destination = directory / f"{hashlib.sha256(attachment_id.encode()).hexdigest()[:12]}-{safe_name}"
        destination.write_bytes(data)
        return destination

    def list_labels(self) -> list[dict[str, str]]:
        return [{"id": str(item.get("id", "")), "name": str(item.get("name", ""))} for item in self.service.users().labels().list(userId="me").execute().get("labels", [])]

    def add_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail:
        result = self.service.users().messages().modify(userId="me", id=message_id, body={"addLabelIds": list(label_ids)}).execute()
        return normalize_google_message(result, include_body=False)

    def remove_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail:
        result = self.service.users().messages().modify(userId="me", id=message_id, body={"removeLabelIds": list(label_ids)}).execute()
        return normalize_google_message(result, include_body=False)

    def archive_email(self, message_id: str) -> GmailEmail:
        return self.remove_labels(message_id, ("INBOX",))

    def create_draft(self, prepared: PreparedEmail) -> str:
        raw = _encode_prepared(prepared)
        result = self.service.users().drafts().create(userId="me", body={"message": {"raw": raw, **({"threadId": prepared.thread_id} if prepared.thread_id else {})}}).execute()
        return str(result.get("id", ""))

    def prepare_email(self, email: PreparedEmail) -> PreparedEmail:
        return email

    def send_prepared(self, email: PreparedEmail) -> str:
        result = self.service.users().messages().send(userId="me", body={"raw": _encode_prepared(email), **({"threadId": email.thread_id} if email.thread_id else {})}).execute()
        return str(result.get("id", ""))


def _encode_prepared(prepared: PreparedEmail) -> str:
    message = EmailMessage()
    message["To"] = ", ".join(prepared.to)
    if prepared.cc:
        message["Cc"] = ", ".join(prepared.cc)
    if prepared.bcc:
        message["Bcc"] = ", ".join(prepared.bcc)
    message["Subject"] = prepared.subject
    if prepared.in_reply_to:
        message["In-Reply-To"] = prepared.in_reply_to
    if prepared.references:
        message["References"] = " ".join(prepared.references)
    message.set_content(prepared.body)
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
