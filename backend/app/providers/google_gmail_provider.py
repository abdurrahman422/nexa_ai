"""Read-only Gmail API provider owned by NEXA.

OAuth is opt-in and configuration-driven. This provider never requests write
scopes and never implements draft creation or sending.
"""

from __future__ import annotations

import json
import os
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
)
from app.schemas.gmail import GmailAttachment, GmailEmail, GmailThread, PreparedEmail


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_SCOPES = (GMAIL_READONLY_SCOPE,)


class GoogleGmailProvider(GmailProvider):
    """Google Gmail implementation for Phase 2A read-only operations."""

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
        """Run the local OAuth flow using only the Gmail read-only scope."""
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
        raise GmailProviderError("Gmail write operations are disabled in Phase 2A.")

    def remove_labels(self, message_id: str, label_ids: Iterable[str]) -> GmailEmail:
        raise GmailProviderError("Gmail write operations are disabled in Phase 2A.")

    def archive_email(self, message_id: str) -> GmailEmail:
        raise GmailProviderError("Gmail write operations are disabled in Phase 2A.")

    def create_draft(self, prepared: PreparedEmail) -> str:
        raise GmailProviderError("Gmail draft creation is disabled in Phase 2A.")

    def prepare_email(self, email: PreparedEmail) -> PreparedEmail:
        raise GmailProviderError("Outgoing email preparation is disabled for the Google provider in Phase 2A.")

    def send_prepared(self, email: PreparedEmail) -> str:
        raise GmailProviderError("Gmail sending is disabled in Phase 2A.")

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

    def _get_credentials(self) -> Credentials:
        self._ensure_active_account()
        credentials: Credentials | None = None
        if self.token_path.is_file():
            try:
                credentials = Credentials.from_authorized_user_file(str(self.token_path), list(GMAIL_SCOPES))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise GmailProviderError("The configured Gmail token file is invalid.") from exc
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as exc:
                raise GmailProviderError("Gmail authorization has expired or was revoked.") from exc
            self._store_credentials(credentials)
        if credentials and credentials.valid:
            return credentials
        raise GmailProviderError("Gmail authorization is required. Start the NEXA Gmail OAuth flow first.")

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
