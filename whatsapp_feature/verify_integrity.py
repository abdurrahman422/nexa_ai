"""Hash existing project files without importing or executing the application."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve().parent


def inventory():
    hashes, unreadable = {}, []
    def error(exc):
        unreadable.append(str(Path(exc.filename).relative_to(ROOT)))
    for base, directories, files in os.walk(ROOT, onerror=error):
        directories[:] = [d for d in directories if Path(base, d) != OWN]
        for name in files:
            path = Path(base, name)
            try:
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(chunk)
                hashes[str(path.relative_to(ROOT))] = digest.hexdigest()
            except OSError:
                unreadable.append(str(path.relative_to(ROOT)))
    return {'files': hashes, 'unreadable': sorted(unreadable)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    path = OWN / 'integrity_baseline.json'
    current = inventory()
    if args.baseline:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(current, stream, indent=2)
        print(json.dumps({'baseline_files': len(current['files']), 'unreadable': current['unreadable']}))
        return
    baseline = json.loads(path.read_text(encoding='utf-8'))
    old, new = baseline['files'], current['files']
    report = {
        'baseline_files': len(old),
        'modified': [p for p in old if p in new and old[p] != new[p]],
        'missing_or_now_unreadable': [p for p in old if p not in new],
        'added_outside_feature': [p for p in new if p not in old],
        'baseline_unreadable': baseline['unreadable'],
        'current_unreadable': current['unreadable'],
    }
    (OWN / 'integrity_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    raise SystemExit(bool(report['modified'] or report['missing_or_now_unreadable'] or report['added_outside_feature']))


if __name__ == '__main__':
    main()
