"""Local, non-secret Gmail account registry and isolated token paths."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

from app.providers.gmail_provider import GmailProviderError


class GmailAccountStore:
    """Manage account metadata without reading or exposing token contents."""

    def __init__(self, root: str | Path | None = None) -> None:
        configured = root or os.getenv("NEXA_GMAIL_ROOT", "")
        self.root = Path(configured).expanduser() if configured else Path.home() / ".nexa_ai" / "gmail"
        self.accounts_dir = self.root / "accounts"
        self.registry_path = self.root / "accounts.json"

    @staticmethod
    def account_id_for_email(email: str) -> str:
        normalized = email.strip().casefold()
        if not normalized or "@" not in normalized:
            raise GmailProviderError("Google did not return a valid Gmail account identity.")
        return hashlib.sha256(f"google:{normalized}".encode("utf-8")).hexdigest()[:24]

    def token_path(self, account_id: str) -> Path:
        if account_id != Path(account_id).name or not account_id.isalnum():
            raise GmailProviderError("Invalid Gmail account identifier.")
        return self.accounts_dir / account_id / "token.json"

    def _load(self) -> dict[str, Any]:
        if not self.registry_path.is_file():
            return {"accounts": [], "active_account_id": None}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise GmailProviderError("The Gmail account registry is invalid.") from exc
        if not isinstance(data, dict) or not isinstance(data.get("accounts", []), list):
            raise GmailProviderError("The Gmail account registry is invalid.")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.registry_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        try:
            temporary.chmod(0o600)
        except OSError:
            pass
        temporary.replace(self.registry_path)
        try:
            self.registry_path.chmod(0o600)
        except OSError:
            pass

    def list_accounts(self) -> list[dict[str, Any]]:
        return [dict(account) for account in self._load().get("accounts", [])]

    def active_account_id(self) -> str | None:
        return self._load().get("active_account_id")

    def active_account(self) -> dict[str, Any] | None:
        active_id = self.active_account_id()
        return next((account for account in self.list_accounts() if account.get("account_id") == active_id), None)

    def active_token_path(self) -> Path:
        account = self.active_account()
        if account is None:
            raise GmailProviderError("Gmail authorization is required. Connect or select a Gmail account first.")
        path = self.token_path(str(account["account_id"]))
        if not path.is_file():
            raise GmailProviderError("The active Gmail account requires authorization again.")
        return path

    def register(self, email: str, *, display_name: str = "", token_path: Path | None = None) -> dict[str, Any]:
        account_id = self.account_id_for_email(email)
        data = self._load()
        accounts = [account for account in data["accounts"] if account.get("account_id") != account_id]
        now = datetime.now(timezone.utc).isoformat()
        existing = next((account for account in data["accounts"] if account.get("account_id") == account_id), {})
        record = {
            "account_id": account_id,
            "email": email.strip(),
            "display_name": display_name,
            "token_path": str((token_path or self.token_path(account_id)).relative_to(self.root)),
            "connected_at": existing.get("connected_at", now),
            "last_used_at": now,
        }
        accounts.append(record)
        data["accounts"] = accounts
        data["active_account_id"] = account_id
        self._save(data)
        return dict(record)

    def switch(self, account_id: str) -> dict[str, Any]:
        account = next((item for item in self.list_accounts() if item.get("account_id") == account_id), None)
        if account is None:
            raise GmailProviderError("The requested Gmail account is not connected.")
        token_path = self.token_path(account_id)
        if not token_path.is_file():
            raise GmailProviderError("The requested Gmail account requires authorization again.")
        data = self._load()
        now = datetime.now(timezone.utc).isoformat()
        for item in data["accounts"]:
            if item.get("account_id") == account_id:
                item["last_used_at"] = now
        data["active_account_id"] = account_id
        self._save(data)
        return dict(account)

    def disconnect(self, account_id: str) -> None:
        data = self._load()
        if not any(account.get("account_id") == account_id for account in data["accounts"]):
            raise GmailProviderError("The requested Gmail account is not connected.")
        token_path = self.token_path(account_id)
        if token_path.is_file():
            token_path.unlink()
        account_dir = token_path.parent
        if account_dir.is_dir() and not any(account_dir.iterdir()):
            account_dir.rmdir()
        data["accounts"] = [account for account in data["accounts"] if account.get("account_id") != account_id]
        if data.get("active_account_id") == account_id:
            data["active_account_id"] = None
        self._save(data)

    def migrate_legacy_token(self, legacy_path: Path, email: str, *, display_name: str = "") -> dict[str, Any] | None:
        if not legacy_path.is_file() or self.active_account() is not None:
            return None
        account_id = self.account_id_for_email(email)
        destination = self.token_path(account_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file():
            shutil.copy2(legacy_path, destination)
            try:
                destination.chmod(0o600)
            except OSError:
                pass
        if not destination.is_file() or destination.stat().st_size != legacy_path.stat().st_size:
            raise GmailProviderError("Legacy Gmail token migration could not be verified.")
        record = self.register(email, display_name=display_name, token_path=destination)
        legacy_path.unlink()
        return record
