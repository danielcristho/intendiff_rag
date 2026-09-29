"""Cache OSV advisory checks for exact npm versions.

    python pipeline/advisories.py --wanted FILE --cache DIR --out FILE
    python pipeline/advisories.py --selfcheck
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://api.osv.dev/v1/querybatch"


def post(queries):
    payload = json.dumps({"queries": queries}).encode()
    req = urllib.request.Request(ENDPOINT, data=payload,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read())
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def check(versions, send=post):
    queries = [{"package": {"name": r["name"], "ecosystem": "npm"},
                "version": r["version"]} for r in versions]
    pending = list(enumerate(queries))
    found = [set() for _ in versions]
    while pending:
        response = send([q for _, q in pending])
        results = response.get("results")
        if not isinstance(results, list) or len(results) != len(pending):
            raise ValueError("OSV response does not match query count")
        remaining = []
        for (index, query), result in zip(pending, results):
            if result.get("error"):
                raise ValueError(f"OSV returned an error: {result['error']}")
            found[index].update(v["id"] for v in result.get("vulns", []))
            if result.get("next_page_token"):
                remaining.append((index, dict(query, page_token=result["next_page_token"])))
        pending = remaining
    stamp = datetime.now(timezone.utc).isoformat()
    return [{"name": row["name"], "version": row["version"],
             "advisory_ids": sorted(ids), "has_advisory": bool(ids),
             "checked_at": stamp, "source": ENDPOINT}
            for row, ids in zip(versions, found)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wanted", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.wanted).read_text().splitlines() if line.strip()]
    versions = list({(r["name"], r["version"]): r for r in rows}.values())
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    with Path(args.out).open("w") as output:
        for start in range(0, len(versions), 100):
            batch = [{"name": r["name"], "version": r["version"]}
                     for r in versions[start:start + 100]]
            key = hashlib.sha256(json.dumps(batch, sort_keys=True).encode()).hexdigest()
            cached = cache / f"{key}.json"
            if not cached.exists():
                cached.write_text(json.dumps(check(batch), indent=2) + "\n")
            checked = json.loads(cached.read_text())
            for row in checked:
                output.write(json.dumps(row) + "\n")
            output.flush()
            print(f"checked {start + len(batch)}/{len(versions)}", flush=True)


def selfcheck():
    calls = []
    def pages(queries):
        calls.append(queries)
        if len(calls) == 1:
            return {"results": [{"vulns": [{"id": "MAL-1"}], "next_page_token": "next"}, {}]}
        assert queries[0]["page_token"] == "next" and len(queries) == 1
        return {"results": [{"vulns": [{"id": "MAL-2"}]}]}
    rows = check([{"name": "a", "version": "1"}, {"name": "b", "version": "2"}], pages)
    assert rows[0]["advisory_ids"] == ["MAL-1", "MAL-2"]
    assert not rows[1]["has_advisory"]
    try:
        check([{"name": "a", "version": "1"}], lambda _: {"results": []})
    except ValueError:
        pass
    else:
        raise AssertionError("missing responses must not become clean advisory checks")
    print("ok")


if __name__ == "__main__":
    selfcheck() if "--selfcheck" in sys.argv else main()
