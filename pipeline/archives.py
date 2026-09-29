"""Extract research ZIP archives as data inside a network-disabled container.

    python pipeline/archives.py ARCHIVE DESTINATION [--prefix MEMBER_PREFIX]
    python pipeline/archives.py --selfcheck
"""
import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


def extract(archive, destination, prefixes=(), password=None):
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"destination must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    extracted, rejected = [], []
    with zipfile.ZipFile(archive) as source:
        selected = [m for m in source.infolist()
                    if not prefixes or any(m.filename.startswith(p) for p in prefixes)]
        if sum(m.file_size for m in selected) > 10 * 1024**3:
            raise ValueError("expanded archive exceeds 10 GiB")
        seen = set()
        accepted = []
        for member in selected:
            name = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            reason = None
            if name.is_absolute() or ".." in name.parts or "\\" in member.filename:
                reason = "unsafe path"
            elif stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                reason = "link or special file"
            elif name in seen:
                reason = "duplicate path"
            elif member.file_size > 512 * 1024**2:
                reason = "member exceeds 512 MiB"
            if reason:
                rejected.append({"member": member.filename, "reason": reason})
                continue
            seen.add(name)
            accepted.append(member)
        # ZipCrypto in Python is slow on multi-gigabyte corpora. Use the system
        # reader only after every member passed the same path/type validation.
        if password and not prefixes and not rejected and shutil.which("unzip"):
            result = subprocess.run(["unzip", "-qq", "-P", password.decode(),
                                     str(archive), "-d", str(destination)],
                                    capture_output=True, timeout=300)
            if result.returncode:
                raise ValueError("unzip failed: " + result.stderr.decode(errors="replace")[:300])
            return {"archive": str(archive), "destination": str(destination),
                    "sha256": hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
                    "files": sum(not m.is_dir() for m in accepted),
                    "bytes": sum(m.file_size for m in accepted), "rejected": []}
        for member in accepted:
            name = PurePosixPath(member.filename)
            target = destination.joinpath(*name.parts)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(member, pwd=password) as incoming, target.open("xb") as output:
                shutil.copyfileobj(incoming, output)
            extracted.append({"member": member.filename, "bytes": member.file_size})
    return {"archive": str(archive), "destination": str(destination),
            "sha256": hashlib.file_digest(Path(archive).open("rb"), "sha256").hexdigest(),
            "files": len(extracted), "bytes": sum(m["bytes"] for m in extracted),
            "rejected": rejected}


def selfcheck():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        archive = root / "sample.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("safe/package.json", '{"name":"example"}')
            output.writestr("../escape", "bad")
            output.writestr("/absolute", "bad")
            link = zipfile.ZipInfo("safe/link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            output.writestr(link, "/etc/passwd")
        report = extract(archive, root / "out")
        assert report["files"] == 1 and len(report["rejected"]) == 3
        assert (root / "out/safe/package.json").exists()
        assert not (root / "escape").exists()
        assert not (root / "out/safe/link").exists()
        try:
            extract(archive, root / "out")
        except ValueError:
            pass
        else:
            raise AssertionError("existing extraction must not be overwritten")
    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("archive")
        parser.add_argument("destination")
        parser.add_argument("--prefix", action="append", default=[])
        parser.add_argument("--password")
        args = parser.parse_args()
        print(json.dumps(extract(args.archive, args.destination, args.prefix,
                                 args.password.encode() if args.password else None)))
