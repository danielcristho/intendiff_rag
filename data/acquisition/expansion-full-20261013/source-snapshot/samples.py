"""Fetch and unpack the sample tarballs listed for the dataset.

Two phases, because §4.1 splits them: `fetch` needs the network and never opens
an archive, `extract` opens archives and must run with no network, for example
`docker run --network none`.

    python pipeline/samples.py fetch --wanted data/wanted.jsonl --out data/samples.jsonl
    python pipeline/samples.py extract --manifest data/samples.jsonl --into work
    python pipeline/samples.py --selfcheck
"""
import argparse
import hashlib
import json
import sys
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path

REGISTRY = "https://registry.npmjs.org"

# npm ships every file under a single top-level directory.
TARBALL_PREFIX = "package"


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# version_url escapes the slash in a scoped name, which the registry needs encoded.
def version_url(name, version):
    return f"{REGISTRY}/{urllib.parse.quote(name, safe='@')}/{version}"


def http_get(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


# tarball_url reads dist.tarball from the version document, per the Registry API.
def tarball_url(name, version, get=http_get):
    document = json.loads(get(version_url(name, version)))
    url = document.get("dist", {}).get("tarball")
    if not url:
        raise LookupError(f"{name}@{version} has no dist.tarball")
    return url


# fetch_one records where the bytes came from, because D59 keeps the replication
# package and the registry apart: a Wyss pair must not silently switch source.
def fetch_one(entry, into, get=http_get):
    name, version = entry["name"], entry["version"]
    target = Path(into) / f"{name.replace('/', '+')}-{version}.tgz"
    target.parent.mkdir(parents=True, exist_ok=True)

    if entry.get("origin") == "replication":
        payload = Path(entry["tarball"]).read_bytes()
    else:
        payload = get(entry.get("tarball") or tarball_url(name, version, get))

    target.write_bytes(payload)
    return {"name": name, "version": version,
            "origin": entry.get("origin", "registry"),
            "tarball": str(target),
            "sha256": hashlib.sha256(payload).hexdigest()}


# unsafe_member names why an archive entry is rejected, or None when it is fine.
# Samples are hostile by assumption, so an archive may try to escape its target
# or plant a link; extraction reads code as data and needs neither.
def unsafe_member(member):
    path = Path(member.name)
    if path.is_absolute() or ".." in path.parts:
        return "path escapes the target directory"
    if member.issym() or member.islnk():
        return "links are not extracted"
    if not (member.isfile() or member.isdir()):
        return "only files and directories are extracted"
    return None


# strip_prefix drops npm's leading `package/` so the version directory holds
# package.json at its root, which the extractor and intent builder expect.
def strip_prefix(name, prefix=TARBALL_PREFIX):
    parts = Path(name).parts
    return str(Path(*parts[1:])) if parts and parts[0] == prefix else name


def extract_one(row, into):
    archive = Path(row["tarball"])
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != row["sha256"]:
        raise ValueError(f"{archive} changed since it was fetched: {digest} != {row['sha256']}")

    target = Path(into) / row["name"] / row["version"]
    target.mkdir(parents=True, exist_ok=True)
    rejected = []
    with tarfile.open(archive, "r:*") as tar:
        for member in tar.getmembers():
            reason = unsafe_member(member)
            if reason:
                rejected.append((member.name, reason))
                continue
            inner = strip_prefix(member.name)
            if not inner or inner == ".":
                continue
            if member.isdir():
                (target / inner).mkdir(parents=True, exist_ok=True)
                continue
            source = tar.extractfile(member)
            if source is None:
                continue
            (target / inner).parent.mkdir(parents=True, exist_ok=True)
            (target / inner).write_bytes(source.read())
    return {"dir": str(target), "rejected": rejected}


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    grab = sub.add_parser("fetch", help="download tarballs and record their checksums")
    grab.add_argument("--wanted", required=True, help="one line per version: name, version, origin")
    grab.add_argument("--into", default="data/tarballs")
    grab.add_argument("--out", required=True)

    open_up = sub.add_parser("extract", help="unpack tarballs; run this without network")
    open_up.add_argument("--manifest", required=True)
    open_up.add_argument("--into", required=True)

    args = parser.parse_args(argv)

    if args.command == "fetch":
        rows = [fetch_one(entry, args.into) for entry in load_jsonl(args.wanted)]
        Path(args.out).write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        print(json.dumps({"fetched": len(rows)}))
        return

    rejected = 0
    for row in load_jsonl(args.manifest):
        result = extract_one(row, args.into)
        rejected += len(result["rejected"])
        for name, reason in result["rejected"]:
            print(f"rejected {row['name']}@{row['version']}: {name} — {reason}", file=sys.stderr)
    print(json.dumps({"extracted": len(load_jsonl(args.manifest)), "rejected": rejected}))


def selfcheck():
    import io
    import tempfile

    tmp = Path(tempfile.mkdtemp())

    assert version_url("@scope/pkg", "1.0.0").endswith("@scope%2Fpkg/1.0.0")
    assert version_url("pkg", "1.0.0").endswith("/pkg/1.0.0")

    document = json.dumps({"dist": {"tarball": "https://example.invalid/p-1.0.0.tgz"}}).encode()
    assert tarball_url("p", "1.0.0", get=lambda url: document) == "https://example.invalid/p-1.0.0.tgz"

    # An archive laid out the way npm lays one out, plus the two shapes a hostile
    # sample can use to reach outside its directory.
    archive = tmp / "p-1.0.0.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, body in (("package/package.json", b'{"name":"p"}'),
                           ("package/lib/index.js", b"module.exports = 1;\n"),
                           ("../escape.js", b"nope"),
                           ("/absolute.js", b"nope")):
            info = tarfile.TarInfo(name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
        link = tarfile.TarInfo("package/link.js")
        link.type, link.linkname = tarfile.SYMTYPE, "/etc/passwd"
        tar.addfile(link)

    payload = archive.read_bytes()
    row = fetch_one({"name": "p", "version": "1.0.0", "origin": "replication",
                     "tarball": str(archive)}, tmp / "tarballs")
    assert row["sha256"] == hashlib.sha256(payload).hexdigest()
    assert row["origin"] == "replication"

    result = extract_one(row, tmp / "work")
    root = Path(result["dir"])

    # npm's leading directory is gone, so package.json sits where the other tools look.
    assert (root / "package.json").read_text() == '{"name":"p"}'
    assert (root / "lib/index.js").exists()

    # Nothing escaped, and no link was planted.
    assert {name for name, _ in result["rejected"]} == {"../escape.js", "/absolute.js", "package/link.js"}
    assert not (tmp / "work/escape.js").exists() and not (root / "link.js").exists()
    assert not list(Path("/").glob("absolute.js"))

    # A tarball that changed after it was recorded must not be unpacked.
    tampered = dict(row, sha256="0" * 64)
    try:
        extract_one(tampered, tmp / "work2")
    except ValueError:
        pass
    else:
        raise AssertionError("a checksum mismatch must stop extraction")

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
