"""Download registry tarballs without installing or opening package contents.

    python pipeline/registry_fetch.py --wanted FILE --out FILE --cache DIR
"""
import argparse
import base64
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


def request(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IntentDiff-RAG-research/1"})
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
        except OSError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)


def integrity_ok(payload, dist):
    integrity = dist.get("integrity", "")
    if integrity:
        supported = []
        for value in integrity.split():
            algorithm, _, encoded = value.partition("-")
            if algorithm in ("sha512", "sha384", "sha256", "sha1"):
                digest = base64.b64encode(hashlib.new(algorithm, payload).digest()).decode()
                supported.append(digest == encoded)
        if not supported:
            raise ValueError("no supported registry integrity algorithm")
        return any(supported)
    if dist.get("shasum"):
        return hashlib.sha1(payload).hexdigest() == dist["shasum"]
    raise ValueError("registry metadata contains no integrity digest")


def fetch(entry, cache):
    name, version = entry["name"], entry["version"]
    identity = f"{name}@{version}"
    key = hashlib.sha256(identity.encode()).hexdigest()
    metadata = cache / "metadata" / f"{key}.json"
    tarball = cache / "tarballs" / f"{key}.tgz"
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@") + "/" + urllib.parse.quote(version, safe="")
    try:
        if not metadata.exists():
            payload = request(url)
            document = json.loads(payload)
            if (document.get("name"), document.get("version")) != (name, version):
                raise ValueError("registry identity differs from requested version")
            metadata.write_bytes(payload)
        document = json.loads(metadata.read_bytes())
        dist = document["dist"]
        source = urllib.parse.urlparse(dist["tarball"])
        if source.scheme != "https" or source.hostname != "registry.npmjs.org":
            raise ValueError("tarball URL is not on the npm registry")
        payload = tarball.read_bytes() if tarball.exists() else request(dist["tarball"])
        if not integrity_ok(payload, dist):
            raise ValueError("registry integrity check failed")
        if not tarball.exists():
            temporary = tarball.with_suffix(".part")
            temporary.write_bytes(payload)
            temporary.rename(tarball)
        return {"name": name, "version": version, "origin": "registry",
                "tarball": str(tarball), "registry_metadata": str(metadata),
                "url": dist["tarball"], "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "registry_integrity_verified": True,
                "retrieved_at": datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        return {"name": name, "version": version, "error": str(exc), "url": url}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wanted", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    cache = Path(args.cache)
    for child in ("metadata", "tarballs"):
        (cache / child).mkdir(parents=True, exist_ok=True)
    wanted = [json.loads(line) for line in Path(args.wanted).read_text().splitlines() if line.strip()]
    seen = set()
    unique = []
    for row in wanted:
        key = row["name"], row["version"]
        if key not in seen:
            seen.add(key)
            unique.append(row)
    success, errors = 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor, Path(args.out).open("w") as output:
        for i, row in enumerate(executor.map(lambda entry: fetch(entry, cache), unique), 1):
            output.write(json.dumps(row) + "\n")
            output.flush()
            if row.get("error"):
                errors += 1
                print(json.dumps(row), flush=True)
            else:
                success += 1
            if i % 50 == 0 or i == len(unique):
                print(json.dumps({"completed": i, "total": len(unique),
                                  "success": success, "errors": errors}), flush=True)


def selfcheck():
    payload = b"registry archive bytes"
    digest = base64.b64encode(hashlib.sha512(payload).digest()).decode()
    assert integrity_ok(payload, {"integrity": "sha512-" + digest})
    assert not integrity_ok(payload + b"changed", {"integrity": "sha512-" + digest})
    assert integrity_ok(payload, {"shasum": hashlib.sha1(payload).hexdigest()})
    for invalid in ({}, {"integrity": "unknown-digest"}):
        try:
            integrity_ok(payload, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("unverifiable archive was accepted")
    print("registry integrity selfcheck passed")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
