"""Scan completed download records in an offline container, then reconcile all pairs."""
import argparse
import json
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

from expansion_screen import inspect_archive, main as finish_screen
from samples import load_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--work', required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    out = Path(args.out)
    wanted = {(r['name'], r['version']) for r in load_jsonl(out / 'wanted.path-b.jsonl')}
    existing = load_jsonl(out / 'version-scans.jsonl')
    completed = {(r['name'], r['version']) for r in existing}
    if not completed <= wanted:
        raise ValueError('Reused scans are outside the frozen version plan')
    submitted = set(completed)
    futures = {}
    errors = sum('error' in r for r in existing)
    last_progress = time.monotonic()
    previous_bytes = -1
    available = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool, (out / 'version-scans.jsonl').open('a') as stream:
        while completed != wanted:
            path = out / 'archives.jsonl'
            size = path.stat().st_size if path.exists() else 0
            if size != previous_bytes:
                # The downloader flushes newline-terminated records; ignore a partial last record.
                payload = path.read_text() if size else ''
                rows = [json.loads(line) for line in payload.split('\n')[:-1] if line]
                available = {(r['name'], r['version']): r for r in rows}
                if not set(available) <= wanted or len(rows) != len(available):
                    raise ValueError('Download identities do not match the frozen plan')
                previous_bytes = size
                last_progress = time.monotonic()
            for key in available.keys() - submitted:
                if len(futures) >= args.workers * 2:
                    break
                futures[pool.submit(inspect_archive, available[key], args.work)] = key
                submitted.add(key)
            if futures:
                done, _ = wait(futures, timeout=2, return_when=FIRST_COMPLETED)
                for future in done:
                    row = future.result()
                    key = futures.pop(future)
                    if key != (row['name'], row['version']):
                        raise ValueError('Scan identity mismatch')
                    stream.write(json.dumps(row) + '\n')
                    stream.flush()
                    completed.add(key)
                    errors += 'error' in row
                    last_progress = time.monotonic()
                    if len(completed) % 100 == 0 or completed == wanted:
                        print(json.dumps({'scanned': len(completed), 'total': len(wanted),
                                          'errors': errors, 'download_records': len(available)}), flush=True)
            else:
                time.sleep(2)
            if time.monotonic() - last_progress > 900:
                raise TimeoutError('No download or scan progress for 15 minutes; resume after inspection')
    finish_screen()


if __name__ == '__main__':
    main()
