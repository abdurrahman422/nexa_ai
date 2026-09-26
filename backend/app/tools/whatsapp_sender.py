"""Visible WhatsApp Web sender with an isolated browser profile and durable ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from urllib.parse import quote

from app.core.runtime_paths import data_dir

PROFILE_DIR = data_dir() / ".whatsapp-profile"
LEDGER_FILE = data_dir() / "whatsapp-send-ledger.json"
_SEND_LOCK = threading.Lock()
_ACTIVE_DRIVER = None


@dataclass
class WhatsAppSendResult:
    status: str
    message: str
    detail: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_ledger() -> dict[str, dict[str, str]]:
    try:
        value = json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_ledger(value: dict[str, dict[str, str]]) -> None:
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_FILE.write_text(json.dumps(value, indent=2), encoding="utf-8")


def _reserve(request_id: str, phone: str, text: str) -> WhatsAppSendResult | None:
    ledger = _read_ledger()
    existing = ledger.get(request_id)
    if existing:
        status = existing.get("status", "unknown")
        if status in {"sent", "submitted", "unknown", "login_required", "failed"}:
            return WhatsAppSendResult(status, existing.get("message", "This send request was already processed."))
    ledger[request_id] = {"status": "reserved", "phone": phone, "text_length": str(len(text)), "created_at": _now()}
    _write_ledger(ledger)
    return None


def _finish(request_id: str, result: WhatsAppSendResult) -> None:
    ledger = _read_ledger()
    entry = ledger.setdefault(request_id, {})
    entry.update({"status": result.status, "message": result.message, "updated_at": _now()})
    _write_ledger(ledger)


def _build_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=NexaWhatsApp")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(options=options)


def _find_first(driver, selectors):
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            continue
    return None


def _logged_in(driver) -> bool:
    return _find_first(driver, ("[data-testid='chat-list']", "#side", "[aria-label='Chat list']")) is not None


def _login_required(driver) -> bool:
    return _find_first(driver, ("canvas[aria-label*='Scan']", "[data-testid='qrcode']", "[data-testid='intro-title']")) is not None


def _verify_visible_phone(driver, phone: str) -> bool:
    digits = "".join(character for character in phone if character.isdigit())
    body_text = (driver.find_element("tag name", "body").text or "").replace(" ", "")
    if digits in body_text or digits[-10:] in body_text:
        return True
    header = _find_first(driver, ("[data-testid='conversation-header']", "header"))
    if header is None:
        return False
    try:
        header.click()
    except Exception:
        return False
    body_text = (driver.find_element("tag name", "body").text or "").replace(" ", "")
    return digits in body_text or digits[-10:] in body_text


def _send_once(driver, phone: str, text: str) -> WhatsAppSendResult:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait

    driver.get(f"https://web.whatsapp.com/send?phone={quote(phone)}")
    wait = WebDriverWait(driver, 20)
    if _login_required(driver) or not _logged_in(driver):
        return WhatsAppSendResult("login_required", "WhatsApp Web login is required. Log in in the Nexa WhatsApp window, then repeat the command.")
    wait.until(lambda current: _find_first(current, ("[data-testid='conversation-panel-body']", "main")) is not None)
    if not _verify_visible_phone(driver, phone):
        return WhatsAppSendResult("wrong_chat", "I could not verify that the open WhatsApp chat belongs to the resolved phone number. Nothing was sent.")
    composer = _find_first(driver, ("[data-testid='conversation-compose-box-input']", "div[contenteditable='true'][role='textbox']"))
    send_button = _find_first(driver, ("[data-testid='send']", "button[aria-label='Send']"))
    if composer is None or send_button is None:
        return WhatsAppSendResult("unknown", "WhatsApp's composer or Send control could not be verified. Delivery is uncertain; check WhatsApp before sending again.")
    composer.click()
    parts = text.split("\n")
    for index, part in enumerate(parts):
        if index:
            composer.send_keys(Keys.SHIFT, Keys.ENTER)
        composer.send_keys(part)
    if composer.text.strip() != text.strip():
        return WhatsAppSendResult("unknown", "The WhatsApp composer did not contain the expected message. Nothing was sent.")
    send_button.click()
    time.sleep(1)
    return WhatsAppSendResult("submitted", "WhatsApp accepted the message for sending. Delivery status is not confirmed; check WhatsApp for sent/delivered status.")


def send_whatsapp_message(request_id: str, phone: str, text: str) -> WhatsAppSendResult:
    """Send once through visible WhatsApp Web; never automatically retry."""
    with _SEND_LOCK:
        duplicate = _reserve(request_id, phone, text)
        if duplicate is not None:
            return duplicate
        global _ACTIVE_DRIVER
        driver = _ACTIVE_DRIVER
        try:
            if driver is None:
                driver = _build_driver()
            result = _send_once(driver, phone, text)
        except Exception:
            result = WhatsAppSendResult("unknown", "WhatsApp send result is uncertain; check WhatsApp before sending again.")
        finally:
            if driver is not None and result.status != "login_required":
                try:
                    driver.quit()
                except Exception:
                    pass
                _ACTIVE_DRIVER = None
            elif result.status == "login_required":
                _ACTIVE_DRIVER = driver
        _finish(request_id, result)
        return result