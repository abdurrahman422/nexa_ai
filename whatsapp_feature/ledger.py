"""Durable click boundary and process lock. A lost/corrupt ledger fails closed."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3


class LedgerError(Exception):
    pass


class BusyError(Exception):
    pass


@contextmanager
def exclusive_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'sender.lock').open('a+b') as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise BusyError('Another WhatsApp operation is active.') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class Ledger:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / 'requests.sqlite3'
        self.marker = self.root / 'ledger.initialized'

    @contextmanager
    def connection(self):
        db = None
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            existed = self.path.exists()
            if self.marker.exists() and not existed:
                raise LedgerError('Previously initialized ledger is missing. Sending is blocked.')
            if existed and self.path.stat().st_size == 0:
                raise LedgerError('Ledger is empty or damaged. Sending is blocked.')
            db = sqlite3.connect(self.path, timeout=5)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA synchronous=FULL')
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise LedgerError('Ledger integrity check failed.')
            if existed:
                # Never silently recreate a dropped requests table.
                db.execute('SELECT request_id, fingerprint, state, message, message_id FROM requests LIMIT 0')
            else:
                db.execute('CREATE TABLE requests (request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL, message TEXT NOT NULL, message_id TEXT NOT NULL DEFAULT \'\', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
                db.commit()
            if not self.marker.exists():
                with self.marker.open('x', encoding='ascii') as stream:
                    stream.write('1\n')
                    stream.flush()
                    os.fsync(stream.fileno())
            yield db
        except (sqlite3.Error, OSError) as exc:
            raise LedgerError('Ledger unavailable or damaged; no automatic reset is allowed.') from exc
        finally:
            if db is not None:
                db.close()

    def reserve(self, request_id, phone, text):
        fingerprint = hashlib.sha256(json.dumps([phone, text], ensure_ascii=False).encode()).hexdigest()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM requests WHERE request_id=?', (request_id,)).fetchone()
            if row:
                if row['fingerprint'] != fingerprint:
                    raise LedgerError('Request ID already belongs to a different recipient or message.')
                if row['state'] not in ('preparing', 'retryable'):
                    return dict(row)
            db.execute('INSERT INTO requests(request_id,fingerprint,state,message) VALUES(?,?,?,?) ON CONFLICT(request_id) DO UPDATE SET state=excluded.state,message=excluded.message,updated_at=CURRENT_TIMESTAMP',
                       (request_id, fingerprint, 'preparing', 'Preparing; Send has not been invoked.'))
            db.commit()
        return None

    def finish(self, request_id, state, message, message_id=''):
        with self.connection() as db:
            cursor = db.execute('UPDATE requests SET state=?,message=?,message_id=?,updated_at=CURRENT_TIMESTAMP WHERE request_id=?',
                                (state, message, message_id, request_id))
            if cursor.rowcount != 1:
                raise LedgerError('Request reservation disappeared.')
            db.commit()

    def status(self, request_id):
        if not self.path.exists() and not self.marker.exists():
            return None
        with self.connection() as db:
            row = db.execute('SELECT request_id,state,message,message_id,updated_at FROM requests WHERE request_id=?', (request_id,)).fetchone()
            return dict(row) if row else None
