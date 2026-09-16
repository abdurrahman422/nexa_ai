"""Gmail API provider owned by NEXA.

OAuth remains opt-in and configuration-driven. Draft creation is the only
Gmail write operation enabled in this phase; sending remains unavailable.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from email.message import EmailMessage
from email.policy import SMTP
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from app.providers.gmail_provider import (
    GmailProvider,
    GmailProviderError,
    _decode_data,
    normalize_google_message,
    safe_text,
)
from app.attachments import resolve_attachments, sanitize_attachment
from app.schemas.gmail import GmailAttachment, GmailDraftSnapshot, GmailEmail, GmailThread, PreparedEmail


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
GMAIL_SCOPES = (GMAIL_READONLY_SCOPE, GMAIL_COMPOSE_SCOPE)


class GoogleGmailProvider(GmailProvider):
    """Google Gmail provider for read operations and Phase 2B draft creation."""

    def __init__(
        self,
        *,
        credentials_path: str | Path | None = None,
        token_path: str | Path | None = None,
        service: Resource | None = None,
        max_attachment_bytes: int = 10 * 1024 * 1024,
    ) -> None:
        self.credentials_path = Path(
            credentials_path
            or os.getenv("NEXA_GMAIL_CREDENTIALS_PATH", "")
            or Path.home() / ".nexa_ai" / "gmail" / "credentials.json"
        ).expanduser()
        self._explicit_token_path = token_path is not None
        self.token_path = Path(token_path or os.getenv("NEXA_GMAIL_TOKEN_PATH", "") or Path.home() / ".nexa_ai" / "gmail" / "token.json").expanduser()
        self.account_id: str | None = None
        self.max_attachment_bytes = max_attachment_bytes
        self._service = service
        self._authorization_lock = Lock()
        self._authorization_state = "idle"
        self._authorization_error: str | None = None
        self.last_draft_metadata: dict[str, Any] = {}

    @property
    def service(self) -> Resource:
        if self._service is None:
            self._service = build("gmail", "v1", credentials=self._get_credentials())
        return self._service

    def auth_status(self) -> dict[str, Any]:
        """Return non-secret OAuth readiness information."""
        with self._authorization_lock:
            authorization_state = self._authorization_state
            authorization_error = self._authorization_error
        try:
            self._ensure_active_account()
        except GmailProviderError:
            return {
                "provider": "google",
                "authenticated": False,
                "state": authorization_state if authorization_state != "idle" else "authorization_required",
                "scope": GMAIL_READONLY_SCOPE,
                "scopes": list(GMAIL_SCOPES),
                "account_id": self.account_id,
                "error": authorization_error,
            }
        credentials_present = self.credentials_path.is_file()
        token_present = self.token_path.is_file()
        if not token_present:
            state = "authorization_required"
        else:
            try:
                credentials = Credentials.from_authorized_user_file(str(self.token_path), list(GMAIL_SCOPES))
            except (OSError, ValueError, json.JSONDecodeError):
                state = "invalid_token_file"
            else:
                state = "ready" if credentials.valid or credentials.refresh_token else "authorization_required"
        return {
            "provider": "google",
            "authenticated": state == "ready",
            "state": state,
            "credentials_path": str(self.credentials_path),
            "token_path": str(self.token_path),
            "scope": GMAIL_READONLY_SCOPE,
            "scopes": list(GMAIL_SCOPES),
            "account_id": self.account_id,
            "authorization_state": authorization_state,
        }

    def begin_authorization(self) -> dict[str, Any]:
        """Start OAuth in a worker so the desktop request remains responsive."""
        with self._authorization_lock:
            if self._authorization_state == "pending":
                return {"provider": "google", "state": "authorization_pending"}
            self._authorization_state = "pending"
            self._authorization_error = None
        Thread(target=self._authorization_worker, name="nexa-gmail-oauth", daemon=True).start()
        return {"provider": "google", "state": "authorization_pending"}

    def authorization_status(self) -> dict[str, Any]:
        with self._authorization_lock:
            return {
                "provider": "google",
                "state": self._authorization_state,
                "error": self._authorization_error,
            }

    def _authorization_worker(self) -> None:
        try:
            self.start_authorization(open_browser=True)
        except Exception as exc:
            with self._authorization_lock:
                self._authorization_state = "error"
                self._authorization_error = str(exc)
        else:
            with self._authorization_lock:
                self._authorization_state = "completed"
                self._authorization_error = None

    def start_authorization(self, *, open_browser: bool = True) -> dict[str, Any]:
        """Run the local OAuth flow with read and draft scopes."""
        if not self.credentials_path.is_file():
            raise GmailProviderError(
                "Gmail OAuth client credentials were not found at the configured path."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_path), list(GMAIL_SCOPES)
        )
        credentials = flow.run_local_server(
            open_browser=open_browser,
            port=0,
            authorization_prompt_message=None,
            timeout_seconds=300,
        )
        email = self._profile_email(credentials)
        store = self._account_store()
        account_id = store.account_id_for_email(email)
        destination = store.token_path(account_id)
        self.token_path = destination
        self._store_credentials(credentials)
        self.account_id = account_id
        store.register(email, token_path=destination)
        self._service = None
        return self.auth_status()

    def list_accounts(self) -> list[dict[str, Any]]:
        return self._account_store().list_accounts()

    def active_account(self) -> dict[str, Any] | None:
        return self._account_store().active_account()

    def switch_account(self, account_id: str) -> dict[str, Any]:
        account = self._account_store().switch(account_id)
        self.account_id = account_id
        self.token_path = self._account_store().token_path(account_id)
        self._service = None
        return account

    def disconnect_account(self, account_id: str) -> None:
        self._account_store().disconnect(account_id)
        if self.account_id == account_id:
            self.account_id = None
            self._service = None
            self.token_path = self._legacy_token_path()

    def search_emails(self, query: str, limit: int = 20) -> list[GmailEmail]:
        references = self._list_message_references(query, limit)
        return [self.get_email(reference["id"], include_body=False) for reference in references]

    def get_email(self, message_id: str, include_body: bool = True) -> GmailEmail:
        message = self.service.users().messages().get(
            userId="me",
            id=message_id,
            format="full" if include_body else "metadata",
        ).execute()
        return normalize_google_message(message, include_body)

    def get_thread(self, thread_id: str, include_body: bool = True) -> GmailThread:
        thread = self.service.users().threads().get(
            userId="me",
            id=thread_id,
            format="full" if include_body else "metadata",
        ).execute()
        return GmailThread(
            str(thread.get("id", thread_id)),
            tuple(normalize_google_message(message, include_body) for message in thread.get("messages", [])),
        )

    def list_attachment_metadata(self, message_id: str) -> list[GmailAttachment]:
        return list(self.get_email(message_id, include_body=True).attachments)

    def download_attachment(self, message_id: str, attachment_id: str, output_dir: str | Path) -> Path:
        metadata = {item.attachment_id: item for item in self.list_attachment_metadata(message_id)}
        attachment = metadata.get(attachment_id)
        if attachment is None:
            raise GmailProviderError("Attachment was not found in the requested message.")
        if attachment.size > self.max_attachment_bytes:
            raise GmailProviderError("Attachment exceeds the configured size limit.")
        response = self.service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=attachment_id
        ).execute()
        data = _decode_data(response.get("data", ""))
        if len(data) > self.max_attachment_bytes:
            raise GmailProviderError("Downloaded attachment exceeds the configured size limit.")
        directory = Path(output_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = Path(attachment.filename).name or f"attachment-{attachment_id}"
        destination = directory / safe_name
        destination.write_bytes(data)
        return destination

    def list_labels(self) -> list[dict[str, str]]:
        response = self.service.users().labels().list(userId="me").execute()
        return [
            {"id": str(label.get("id", "")), "name": str(label.get("name", ""))}
            for label in response.get("labels", [])
        ]

    def add_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail:
        raise GmailProviderError("Gmail label mutations are disabled in Phase 2B.")

    def remove_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail:
        raise GmailProviderError("Gmail label mutations are disabled in Phase 2B.")

    def archive_email(self, message_id: str) -> GmailEmail:
        raise GmailProviderError("Gmail archive mutations are disabled in Phase 2B.")

    def create_draft(self, prepared: PreparedEmail) -> str:
        self._validate_outgoing_recipients(prepared)
        credentials = self._get_credentials(require_compose=True)
        message = self._build_plain_draft_message(prepared)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        payload: dict[str, Any] = {"message": {"raw": raw}}
        if prepared.thread_id:
            payload["message"]["threadId"] = prepared.thread_id
        response = self.service.users().drafts().create(userId="me", body=payload).execute()
        api_draft_id = str(response.get("id", ""))
        if not api_draft_id:
            raise GmailProviderError("Gmail did not return a draft identifier.")
        draft_message = response.get("message", {}) or {}
        readback = self.service.users().drafts().get(
            userId="me", id=api_draft_id, format="raw"
        ).execute()
        readback_message = readback.get("message", {}) or {}
        raw_message = readback_message.get("raw")
        if not isinstance(raw_message, str) or not raw_message:
            raise GmailProviderError("Gmail draft verification did not return the stored MIME message.")
        try:
            parsed_message = BytesParser(policy=SMTP).parsebytes(_decode_data(raw_message))
            stored_body = parsed_message.get_body(preferencelist=("plain", "html"))
            stored_body_text = stored_body.get_content() if stored_body else ""
            stored_subject = str(parsed_message.get("Subject", ""))
        except (ValueError, TypeError) as exc:
            raise GmailProviderError("Gmail draft verification returned malformed MIME data.") from exc
        expected_body = prepared.body.replace("\r\n", "\n")
        normalized_stored_body = stored_body_text.replace("\r\n", "\n")
        body_present = expected_body in normalized_stored_body
        if not body_present:
            raise GmailProviderError("Gmail draft verification could not find the stored reply body.")
        message_id = str(readback_message.get("id", "") or draft_message.get("id", "")) or None
        thread_id = str(readback_message.get("threadId", "") or draft_message.get("threadId", "") or prepared.thread_id) or None
        active_account = self.active_account() or {}
        self.last_draft_metadata = {
            "draft_id": api_draft_id,
            "api_draft_id": api_draft_id,
            "message_id": message_id,
            "thread_id": thread_id,
            "body_present": body_present,
            "body_preview": safe_text(stored_body_text, 160),
            "subject": stored_subject or prepared.subject,
            "active_account": {
                "account_id": str(active_account.get("account_id", "")) or None,
                "email": str(active_account.get("email", "")) or None,
            },
            "to": list(prepared.to),
            "cc": list(prepared.cc),
            "bcc": list(prepared.bcc),
            "subject": prepared.subject,
            "attachment_metadata": [
                sanitize_attachment(item) for item in prepared.attachments
            ],
        }
        return api_draft_id

    def get_draft_snapshot(self, draft_id: str) -> GmailDraftSnapshot:
        self._get_credentials()
        response = self.service.users().drafts().get(
            userId="me", id=draft_id, format="raw"
        ).execute()
        message = response.get("message", {}) or {}
        raw_message = message.get("raw")
        if not isinstance(raw_message, str) or not raw_message:
            raise GmailProviderError("Gmail draft verification did not return the stored MIME message.")
        try:
            parsed = BytesParser(policy=SMTP).parsebytes(_decode_data(raw_message))
            body_part = parsed.get_body(preferencelist=("plain", "html"))
            body = body_part.get_content() if body_part else ""
            attachments: list[dict[str, Any]] = []
            for part in parsed.iter_attachments():
                payload = part.get_payload(decode=True) or b""
                filename = str(part.get_filename() or "")
                mime_type = part.get_content_type()
                attachments.append({
                    "filename": filename,
                    "mime_type": mime_type,
                    "size": len(payload),
                    "attachment_id": "",
                    "content_sha256": hashlib.sha256(payload).hexdigest(),
                })
            email = PreparedEmail(
                to=tuple(address for _, address in getaddresses([str(parsed.get("To", ""))]) if address),
                cc=tuple(address for _, address in getaddresses([str(parsed.get("Cc", ""))]) if address),
                bcc=tuple(address for _, address in getaddresses([str(parsed.get("Bcc", ""))]) if address),
                subject=str(parsed.get("Subject", "")),
                body=body,
                attachments=tuple(
                    GmailAttachment(item["filename"], item["mime_type"], item["size"], item["attachment_id"])
                    for item in attachments
                ),
                thread_id=str(message.get("threadId", "")) or None,
                in_reply_to=str(parsed.get("In-Reply-To", "")) or None,
                references=tuple(str(parsed.get("References", "")).split()),
            )
        except (TypeError, ValueError) as exc:
            raise GmailProviderError("Gmail draft verification returned malformed MIME data.") from exc
        return GmailDraftSnapshot(draft_id, email, tuple(attachments))

    @staticmethod
    def _build_plain_draft_message(prepared: PreparedEmail) -> EmailMessage:
        message = EmailMessage(policy=SMTP)
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

        # Keep the normal email/reply body as the primary editable body.
        message.set_content(prepared.body, subtype="plain")

        # Revalidate every local attachment immediately before reading it.
        if prepared.attachments:
            local_paths: list[str] = []

            for attachment in prepared.attachments:
                if not attachment.local_path:
                    raise GmailProviderError(
                        f"Attachment has no validated local file path: {attachment.filename}."
                    )
                local_paths.append(attachment.local_path)

            validated_attachments = resolve_attachments(local_paths)

            for attachment in validated_attachments:
                path = Path(attachment.local_path)

                try:
                    file_bytes = path.read_bytes()
                except OSError as exc:
                    raise GmailProviderError(
                        f"Attachment is not readable: {attachment.filename}."
                    ) from exc

                mime_type = attachment.mime_type or "application/octet-stream"

                if "/" in mime_type:
                    maintype, subtype = mime_type.split("/", 1)
                else:
                    maintype, subtype = "application", "octet-stream"

                message.add_attachment(
                    file_bytes,
                    maintype=maintype,
                    subtype=subtype,
                    filename=attachment.filename,
                )

        return message

    def prepare_email(self, email: PreparedEmail) -> PreparedEmail:
        raise GmailProviderError("Separate outgoing preparation is not supported; create a Gmail draft instead.")

    def send_prepared(self, email: PreparedEmail) -> str:
        raise GmailProviderError("Gmail sending is disabled in Phase 2B; review and send the draft manually in Gmail.")

    def _list_message_references(self, query: str, limit: int) -> list[dict[str, str]]:
        remaining = max(1, min(limit, 100))
        page_token: str | None = None
        references: list[dict[str, str]] = []
        while remaining > 0:
            response = self.service.users().messages().list(
                userId="me",
                q=query or None,
                maxResults=remaining,
                pageToken=page_token,
            ).execute()
            page = response.get("messages", []) or []
            references.extend(page[:remaining])
            remaining -= len(page)
            page_token = response.get("nextPageToken")
            if not page_token or not page:
                break
        return references[: max(1, min(limit, 100))]

    def _get_credentials(self, *, require_compose: bool = False) -> Credentials:
        self._ensure_active_account()
        credentials: Credentials | None = None
        if self.token_path.is_file():
            try:
                credentials = Credentials.from_authorized_user_file(str(self.token_path), list(GMAIL_SCOPES))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise GmailProviderError("The configured Gmail token file is invalid.") from exc
        if require_compose and credentials and not self._has_compose_scope(credentials):
            raise GmailProviderError("Gmail draft creation requires reconnecting this account to grant Gmail compose access.")
        if require_compose and credentials and GMAIL_COMPOSE_SCOPE not in self._stored_scopes():
            raise GmailProviderError("Gmail draft creation requires reconnecting this account to grant Gmail compose access.")
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as exc:
                raise GmailProviderError("Gmail authorization has expired or was revoked.") from exc
            self._store_credentials(credentials)
        if credentials and credentials.valid:
            return credentials
        raise GmailProviderError("Gmail authorization is required. Start the NEXA Gmail OAuth flow first.")

    @staticmethod
    def _has_compose_scope(credentials: Credentials) -> bool:
        return GMAIL_COMPOSE_SCOPE in set(credentials.scopes or ())

    def _stored_scopes(self) -> set[str]:
        try:
            data = json.loads(self.token_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise GmailProviderError("The configured Gmail token file is invalid.") from exc
        scopes = data.get("scopes", []) if isinstance(data, dict) else []
        return {str(scope) for scope in scopes} if isinstance(scopes, list) else set()

    @staticmethod
    def _validate_outgoing_recipients(prepared: PreparedEmail) -> None:
        try:
            addresses = (*prepared.to, *prepared.cc, *prepared.bcc)
        except TypeError as exc:
            raise GmailProviderError("Gmail draft creation is disabled for invalid prepared email input.") from exc
        if not addresses:
            raise GmailProviderError("At least one recipient is required.")
        for value in addresses:
            if any(character in value for character in ("\r", "\n")):
                raise GmailProviderError("Email headers must not contain line breaks.")
            parsed = getaddresses([value])
            if len(parsed) != 1 or not parsed[0][1] or parsed[0][1] != value.strip() or "@" not in parsed[0][1]:
                raise GmailProviderError("Invalid recipient email address.")
        if any(character in prepared.subject for character in ("\r", "\n")):
            raise GmailProviderError("Email content must not contain header line breaks.")

    def _store_credentials(self, credentials: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(credentials.to_json(), encoding="utf-8")
        try:
            self.token_path.chmod(0o600)
        except OSError:
            pass

    def _account_store(self):
        from app.gmail_accounts import GmailAccountStore

        return GmailAccountStore()

    def _legacy_token_path(self) -> Path:
        configured = os.getenv("NEXA_GMAIL_TOKEN_PATH", "")
        return Path(configured).expanduser() if configured else Path.home() / ".nexa_ai" / "gmail" / "token.json"

    def _ensure_active_account(self) -> None:
        if self._explicit_token_path:
            return
        store = self._account_store()
        active = store.active_account()
        if active is not None:
            self.account_id = str(active["account_id"])
            self.token_path = store.active_token_path()
            return
        legacy = self._legacy_token_path()
        if not legacy.is_file():
            raise GmailProviderError("Gmail authorization is required. Connect or select a Gmail account first.")
        credentials = self._credentials_from_path(legacy)
        email = self._profile_email(credentials)
        record = store.migrate_legacy_token(legacy, email)
        if record is None:
            raise GmailProviderError("Gmail authorization is required. Connect or select a Gmail account first.")
        self.account_id = str(record["account_id"])
        self.token_path = store.active_token_path()

    def _credentials_from_path(self, path: Path) -> Credentials:
        try:
            credentials = Credentials.from_authorized_user_file(str(path), list(GMAIL_SCOPES))
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            if not credentials.valid:
                raise GmailProviderError("Gmail authorization has expired or was revoked.")
            return credentials
        except GmailProviderError:
            raise
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise GmailProviderError("The configured Gmail token file is invalid.") from exc

    def _profile_email(self, credentials: Credentials) -> str:
        try:
            service = build("gmail", "v1", credentials=credentials)
            profile = service.users().getProfile(userId="me").execute()
            email = str(profile.get("emailAddress", "")).strip()
        except Exception as exc:
            raise GmailProviderError("Unable to identify the authorized Google account.") from exc
        if not email:
            raise GmailProviderError("Google did not return the authorized account identity.")
        return email
