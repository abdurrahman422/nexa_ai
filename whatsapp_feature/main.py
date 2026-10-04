"""Standalone CLI. Importing this module never starts Chrome or sends messages."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .browser import BrowserPool
from .ledger import Ledger, LedgerError, exclusive_lock
from .models import Result
from .service import Sender

ROOT = Path(__file__).resolve().parent


def make_parser():
    parser = argparse.ArgumentParser(description='Nexa WhatsApp text-send extension (live sending requires --allow-send).')
    parser.add_argument('--state-dir', type=Path, default=ROOT / 'state')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Read-only dependency/readiness report; no Chrome or network.')
    status = sub.add_parser('status', help='Read the durable result for one request ID.')
    status.add_argument('request_id')
    draft = sub.add_parser('draft', help='Return local draft text; never open browser or send.')
    draft.add_argument('--phone', required=True)
    draft.add_argument('--text', required=True)
    send = sub.add_parser('send', help='Explicitly send text to a phone number.')
    send.add_argument('--phone', required=True)
    send.add_argument('--text', required=True)
    send.add_argument('--request-id', required=True)
    send.add_argument('--allow-send', action='store_true')
    sub.add_parser('connect', help='Open visible WhatsApp Web for QR login only. Does not queue a send.')
    return parser


def main(argv=None):
    sys.dont_write_bytecode = True
    args = make_parser().parse_args(argv)
    if args.command == 'doctor':
        from importlib.util import find_spec
        result = {'selenium_available': find_spec('selenium') is not None,
                  'state_directory': str(args.state_dir.resolve()),
                  'live_browser_verified': False, 'live_delivery_verified': False,
                  'note': 'Chrome and a logged-in dedicated WhatsApp Web profile are needed. No messages sent.'}
    elif args.command == 'draft':
        from .models import validate_request
        try:
            phone = validate_request('draft', args.phone, args.text)
            result = {'status': 'draft', 'phone': phone, 'text': args.text, 'sent': False}
        except ValueError as exc:
            result = asdict(Result('invalid_request', str(exc)))
    elif args.command == 'status':
        try:
            with exclusive_lock(args.state_dir):
                result = Ledger(args.state_dir).status(args.request_id) or {'status': 'not_found'}
        except Exception as exc:
            result = {'status': 'unavailable', 'message': str(exc)}
    elif args.command == 'connect':
        pool = BrowserPool(args.state_dir / 'chrome-profile')
        try:
            with exclusive_lock(args.state_dir):
                browser = pool()
                browser.driver.get('https://web.whatsapp.com')
                input('Complete QR login in the visible browser, then press Enter here to close it. No message will be sent. ')
                result = {'status': 'connection_window_closed', 'note': 'Login readiness is verified on the next explicit send.'}
        except Exception:
            result = {'status': 'unavailable', 'message': 'Could not complete the login window. Check Chrome/dependencies; no message sent.'}
        finally:
            pool.shutdown()
    else:
        pool = BrowserPool(args.state_dir / 'chrome-profile')
        result = asdict(Sender(args.state_dir, pool).send(args.request_id, args.phone, args.text, enabled=args.allow_send))
        if result['status'] == 'login_required':
            print(json.dumps(result, ensure_ascii=False))
            try:
                input('After scanning the QR code, press Enter. This exits without sending; rerun the same explicit command and ID. ')
            except EOFError:
                pass
            pool.shutdown()
            return
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
