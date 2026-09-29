"""Unpack the archives an extraction plan lists; runs offline."""
import argparse
import tarfile
import zipfile
from pathlib import Path

from pipeline.shared.hashing import sha256_file
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl

# MAX_UNPACKED keeps an archive bomb from filling the disk; a plan row may set a lower cap.
MAX_UNPACKED = 2 * 2**30


# plan_row describes one archive to unpack; the optional fields stay out when unset.
def plan_row(archive, target, sha256=None, password=None, max_bytes=None):
    row = {"archive": str(archive), "target": str(target)}
    for key, value in (("sha256", sha256), ("password", password), ("max_bytes", max_bytes)):
        if value:
            row[key] = value
    return row


def write_plan(path, rows):
    write_jsonl(path, rows)


def has_files(directory):
    return directory.is_dir() and any(path.is_file() for path in directory.rglob("*"))


# unpack_one extracts an archive into its target and returns None, "cached", or why it failed.
def unpack_one(row):
    archive, target = Path(row["archive"]), Path(row["target"])
    if has_files(target):
        return "cached"
    if not archive.is_file():
        return "missing archive"
    if row.get("sha256") and sha256_file(archive) != row["sha256"]:
        return "checksum mismatch"
    limit = row.get("max_bytes", MAX_UNPACKED)
    target.mkdir(parents=True, exist_ok=True)
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as bundle:
                if sum(info.file_size for info in bundle.infolist()) > limit:
                    return "too large"
                # ZipFile.extractall strips absolute paths and ".." and creates no symlinks.
                password = row.get("password")
                bundle.extractall(target, pwd=password.encode() if password else None)
        else:
            with tarfile.open(archive, "r:*") as bundle:
                if sum(member.size for member in bundle.getmembers()) > limit:
                    return "too large"
                # filter="data" refuses absolute paths, links out of target and "..".
                bundle.extractall(target, filter="data")
    except (tarfile.TarError, zipfile.BadZipFile, RuntimeError, OSError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def run_plan(rows, log=print):
    failed = []
    for row in rows:
        why = unpack_one(row)
        if why and why != "cached":
            failed.append((row["archive"], why))
            log(f"  failed {row['archive']}: {why}")
    return failed


def main(argv=None):
    parser = argparse.ArgumentParser(prog="extract")
    parser.add_argument("--plan", required=True, action="append")
    args = parser.parse_args(argv)
    require_offline()
    rows = [row for plan in args.plan for row in read_jsonl(plan)]
    # A failure is reported, not fatal: the next step reads a missing directory as "not extracted".
    failed = run_plan(rows)
    print(f"{len(rows) - len(failed)} of {len(rows)} archives unpacked")
