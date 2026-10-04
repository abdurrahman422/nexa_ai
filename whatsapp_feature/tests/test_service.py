import contextlib
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from whatsapp_feature.ledger import Ledger, LedgerError, exclusive_lock
from whatsapp_feature.models import BeforeSendError, Result, normalize_phone
from whatsapp_feature.service import Sender
from whatsapp_feature.main import main


class FakeBrowser:
    def __init__(self):
        self.calls = []
        self.clicks = 0
        self.fail_at = None
        self.failure = RuntimeError('browser failure')
        self.result = Result('sent', 'Sent acknowledgement verified.', message_id='true_id')
        self.closed = []

    def call(self, name):
        self.calls.append(name)
        if self.fail_at == name:
            raise self.failure

    def open_chat(self, phone): self.call('open')
    def verify_recipient(self, phone): self.call('verify')
    def compose(self, text): self.call('compose')
    def prepare_send(self, phone, text):
        self.call('prepare')
        return self
    def outgoing_ids(self):
        self.call('baseline')
        return {'old'}
    def click(self):
        self.clicks += 1
        self.call('click')
    def observe_result(self, text, previous):
        assert previous == {'old'}
        self.call('observe')
        return self.result
    def close(self, keep_open=False): self.closed.append(keep_open)


class SenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.browser = FakeBrowser()
        self.sender = Sender(self.root, lambda: self.browser)

    def send(self, **kwargs):
        return self.sender.send(kwargs.pop('request_id', 'turn1'), kwargs.pop('phone', '01712345678'),
                                kwargs.pop('text', 'hello'), enabled=kwargs.pop('enabled', True), **kwargs)

    def test_disabled_never_opens_browser_or_creates_ledger(self):
        self.assertEqual(self.send(enabled=False).status, 'blocked')
        self.assertFalse(self.sender.ledger.path.exists())
        self.assertEqual(self.browser.calls, [])

    def test_valid_send_has_ordered_boundary_and_ack(self):
        self.assertEqual(self.send().status, 'sent')
        self.assertEqual(self.browser.calls, ['open', 'verify', 'compose', 'prepare', 'baseline', 'click', 'observe'])
        self.assertEqual(self.browser.clicks, 1)

    def test_invalid_phone_never_opens_browser(self):
        for phone in ('Rahim', 'abc01712345678', '123', '01712345678@evil', '00000000'):
            with self.subTest(phone=phone):
                self.assertEqual(self.send(phone=phone).status, 'invalid_request')
        self.assertEqual(self.browser.calls, [])

    def test_invalid_text_never_opens_browser(self):
        for text in ('', ' ', '\ue007', 'a\x00b', 'a\tb', 'x' * 10001):
            with self.subTest(text=repr(text[:10])):
                self.assertEqual(self.send(text=text).status, 'invalid_request')
        self.assertEqual(self.browser.calls, [])

    def test_stable_id_required(self):
        for request_id in ('', None, '../id', 'x' * 129):
            self.assertEqual(self.send(request_id=request_id).status, 'invalid_request')

    def test_login_retry_same_id_after_login(self):
        self.browser.fail_at = 'open'
        self.browser.failure = BeforeSendError('login_required', 'Log in, then repeat.')
        self.assertEqual(self.send().status, 'login_required')
        self.assertEqual(self.browser.closed, [True])
        self.assertEqual(self.browser.clicks, 0)
        self.browser.fail_at = None
        self.assertEqual(self.send().status, 'sent')
        self.assertEqual(self.browser.clicks, 1)

    def test_retry_before_click_does_not_duplicate(self):
        for phase in ('open', 'verify', 'compose', 'prepare', 'baseline'):
            with self.subTest(phase=phase):
                self.browser.fail_at = phase
                result = self.send(request_id=phase)
                self.assertTrue(result.retryable)
                self.browser.fail_at = None
                self.assertEqual(self.send(request_id=phase).status, 'sent')
        self.assertEqual(self.browser.clicks, 5)

    def test_wrong_chat_no_click(self):
        self.browser.fail_at = 'verify'
        self.browser.failure = BeforeSendError('wrong_chat', 'Mismatch')
        self.assertEqual(self.send().status, 'wrong_chat')
        self.assertEqual(self.browser.clicks, 0)

    def test_send_exception_never_retries(self):
        self.browser.fail_at = 'click'
        self.assertEqual(self.send().status, 'unknown')
        self.browser.fail_at = None
        self.assertEqual(self.send().status, 'unknown')
        self.assertEqual(self.browser.clicks, 1)

    def test_observation_exception_never_retries(self):
        self.browser.fail_at = 'observe'
        self.assertEqual(self.send().status, 'unknown')
        self.assertEqual(self.send().status, 'unknown')
        self.assertEqual(self.browser.clicks, 1)

    def test_terminal_states_are_deduplicated(self):
        for state in ('submitted', 'sent', 'delivered', 'read', 'unknown'):
            self.browser.result = Result(state, state)
            self.assertEqual(self.send(request_id=state).status, state)
            self.assertEqual(self.send(request_id=state).status, state)
        self.assertEqual(self.browser.clicks, 5)

    def test_duplicate_after_process_restart(self):
        self.send()
        fresh = Sender(self.root, lambda: self.fail('Browser must not be started'))
        self.assertEqual(fresh.send('turn1', '01712345678', 'hello', enabled=True).status, 'sent')

    def test_reused_id_different_body_or_recipient_rejected(self):
        self.send()
        self.assertEqual(self.send(text='different').status, 'ledger_error')
        self.assertEqual(self.send(phone='01712345679').status, 'ledger_error')
        self.assertEqual(self.browser.clicks, 1)

    def test_crash_before_boundary_can_retry(self):
        self.sender.ledger.reserve('turn1', '8801712345678', 'hello')
        self.assertEqual(self.send().status, 'sent')

    def test_crash_after_boundary_cannot_retry(self):
        self.sender.ledger.reserve('turn1', '8801712345678', 'hello')
        self.sender.ledger.finish('turn1', 'sending', 'Possible send')
        self.assertEqual(self.send().status, 'unknown')
        self.assertEqual(self.browser.clicks, 0)

    def test_corrupt_ledger_fails_closed(self):
        self.sender.ledger.path.write_bytes(b'not a database')
        self.assertEqual(self.send().status, 'ledger_error')
        self.assertEqual(self.browser.calls, [])

    def test_missing_ledger_with_marker_fails_closed(self):
        self.sender.ledger.marker.write_text('1')
        self.assertEqual(self.send().status, 'ledger_error')
        self.assertEqual(self.browser.calls, [])

    def test_empty_ledger_fails_closed(self):
        self.sender.ledger.path.touch()
        self.assertEqual(self.send().status, 'ledger_error')

    def test_missing_table_is_not_silently_recreated(self):
        with contextlib.closing(sqlite3.connect(self.sender.ledger.path)) as db:
            db.execute('CREATE TABLE wrong(value TEXT)')
            db.commit()
        self.assertEqual(self.send().status, 'ledger_error')

    def test_competing_operation_is_busy(self):
        with exclusive_lock(self.root):
            self.assertEqual(self.send().status, 'busy')
        self.assertEqual(self.browser.calls, [])

    def test_boundary_commit_failure_prevents_click(self):
        real = self.sender.ledger.finish
        def fail_boundary(request_id, state, message, message_id=''):
            if state == 'sending': raise LedgerError('disk failed')
            real(request_id, state, message, message_id)
        with patch.object(self.sender.ledger, 'finish', side_effect=fail_boundary):
            self.assertEqual(self.send().status, 'ledger_error')
        self.assertEqual(self.browser.clicks, 0)

    def test_result_commit_failure_blocks_next_attempt(self):
        real = self.sender.ledger.finish
        def fail_result(request_id, state, message, message_id=''):
            if state == 'sent': raise LedgerError('disk failed')
            real(request_id, state, message, message_id)
        with patch.object(self.sender.ledger, 'finish', side_effect=fail_result):
            self.assertEqual(self.send().status, 'unknown')
        self.assertEqual(self.send().status, 'unknown')
        self.assertEqual(self.browser.clicks, 1)

    def test_ledger_does_not_store_message_or_phone(self):
        self.send(text='private secret message')
        data = self.sender.ledger.path.read_bytes()
        self.assertNotIn(b'private secret message', data)
        self.assertNotIn(b'8801712345678', data)

    def test_international_and_bangladesh_normalization(self):
        self.assertEqual(normalize_phone('+1 (415) 555-0123'), '14155550123')
        self.assertEqual(normalize_phone('01712345678'), '8801712345678')
        self.assertEqual(normalize_phone('008801712345678'), '8801712345678')

    def test_cli_draft_never_constructs_browser(self):
        with patch('whatsapp_feature.main.BrowserPool', side_effect=AssertionError('browser forbidden')):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main(['draft', '--phone', '01712345678', '--text', 'hello'])
        self.assertIn('"sent": false', output.getvalue())

    def test_cli_send_without_allow_send_is_blocked(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            main(['--state-dir', str(self.root), 'send', '--phone', '01712345678', '--text', 'hello', '--request-id', 'x'])
        self.assertIn('blocked', output.getvalue())
        self.assertFalse(self.sender.ledger.path.exists())


if __name__ == '__main__':
    unittest.main()
