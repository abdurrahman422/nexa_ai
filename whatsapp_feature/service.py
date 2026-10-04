"""Sending policy independent of Selenium; injectable browser enables offline tests."""
from .ledger import Ledger, LedgerError, BusyError, exclusive_lock
from .models import BeforeSendError, Result, validate_request


class Sender:
    def __init__(self, root, browser_factory):
        self.root = root
        self.ledger = Ledger(root)
        self.browser_factory = browser_factory

    def send(self, request_id, phone, text, *, enabled=False):
        if not enabled:
            return Result('blocked', 'WhatsApp sending is disabled. Enable it before an explicit send command.')
        try:
            phone = validate_request(request_id, phone, text)
        except ValueError as exc:
            return Result('invalid_request', str(exc))
        try:
            with exclusive_lock(self.root):
                return self._send_locked(request_id, phone, text)
        except BusyError as exc:
            return Result('busy', str(exc), True)
        except LedgerError as exc:
            return Result('ledger_error', str(exc))
        except OSError:
            return Result('unavailable', 'The isolated state directory is unavailable. Nothing was sent.', True)

    def _send_locked(self, request_id, phone, text):
        existing = self.ledger.reserve(request_id, phone, text)
        if existing:
            if existing['state'] in ('sending', 'unknown'):
                return Result('unknown', 'This request may already have been sent. Check WhatsApp; it will not be sent again automatically.')
            return Result(existing['state'], existing['message'], False, existing['message_id'])
        browser = None
        click_boundary = False
        keep_open = False
        try:
            browser = self.browser_factory()
            browser.open_chat(phone)
            browser.verify_recipient(phone)
            browser.compose(text)
            # Resolve button AFTER composing. Verify identity and exact text again.
            button = browser.prepare_send(phone, text)
            previous = browser.outgoing_ids()
            self.ledger.finish(request_id, 'sending', 'Send may be invoked. Never automatically retry this request.')
            click_boundary = True
            button.click()  # Exactly one invocation; an exception is still ambiguous.
            result = browser.observe_result(text, previous)
            if result.status not in ('submitted', 'sent', 'delivered', 'read', 'unknown'):
                result = Result('unknown', 'Unrecognized browser result. Check WhatsApp before any new request.')
            self.ledger.finish(request_id, result.status, result.message, result.message_id)
            return result
        except LedgerError:
            if click_boundary:
                return Result('unknown', 'Send may have happened; its result could not be saved. Do not create a new request ID.')
            raise
        except Exception as exc:
            if click_boundary:
                result = Result('unknown', 'Send may have happened. Check WhatsApp; no automatic retry will occur.')
                try:
                    self.ledger.finish(request_id, 'unknown', result.message)
                except LedgerError:
                    pass  # The durable sending boundary still prevents retries.
                return result
            if isinstance(exc, BeforeSendError):
                keep_open = exc.status == 'login_required'
                result = Result(exc.status, str(exc), True)
            else:
                result = Result('unavailable', 'Browser or network failed before Send. Resolve the issue and repeat the same request ID.', True)
            self.ledger.finish(request_id, 'retryable', result.message)
            return result
        finally:
            if browser is not None:
                try:
                    browser.close(keep_open=keep_open)
                except Exception:
                    pass
