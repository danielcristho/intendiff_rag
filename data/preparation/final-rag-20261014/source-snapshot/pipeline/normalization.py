"""Prepare isolated version trees with the pinned static normalizer.

    python pipeline/normalization.py --selfcheck
"""
import fnmatch
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

VERSION = "static-dolos-exact-v2"
MAX_SOURCE_BYTES = 4 * 1024**2
EXCLUDED = ("*.wasm", "*.md", "*.map", ".npmignore", "LICENSE*", "license*",
            "*.tsbuildinfo", "package-lock.json", "yarn.lock")


def files(root):
    found = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(fnmatch.fnmatch(part, pattern) for part in relative.parts for pattern in EXCLUDED):
            continue
        if path.is_symlink():
            raise ValueError(f"unexpected symlink: {relative}")
        if path.is_file():
            found[relative.as_posix()] = path
    return found


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def normalize_jobs(jobs, directory):
    if not shutil.which("normalize-pair"):
        raise RuntimeError("normalize-pair is required; run in the pinned preprocessing container")
    cache = Path(os.environ["INTENDIFF_NORMALIZE_CACHE"]) if os.environ.get("INTENDIFF_NORMALIZE_CACHE") else None
    executable = Path(shutil.which("normalize-pair")).resolve()
    engine = digest(executable).hex()
    lockfile = executable.parent / "package-lock.json"
    if lockfile.exists():
        engine += digest(lockfile).hex()
    results, pending, keys = {}, [], {}
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        identity = {"engine": engine, "version": VERSION,
                    "mode": "javascript" if job["path"].endswith("js") else "typescript",
                    "before": job["before"], "after": job["after"]}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        keys[job["path"]] = key
        target = cache / (key + ".json.gz") if cache else None
        if target and target.exists():
            with gzip.open(target, "rt") as stream:
                row = json.load(stream)
            results[job["path"]] = dict(row, path=job["path"])
        else:
            pending.append(job)
    if not pending:
        return [results[job["path"]] for job in jobs]
    request = directory / "jobs.json"
    request.write_text(json.dumps(pending))
    result = subprocess.run(["normalize-pair", str(request)], capture_output=True,
                            text=True, timeout=300, check=True)
    rows = json.loads(result.stdout)
    if [r["path"] for r in rows] != [r["path"] for r in pending]:
        raise ValueError("normalizer returned mismatching file identities")
    for row in rows:
        results[row["path"]] = row
        if cache:
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temporary:
                temporary.write(gzip.compress(json.dumps(row).encode()))
            Path(temporary.name).replace(cache / (keys[row["path"]] + ".json.gz"))
    return [results[job["path"]] for job in jobs]


@contextmanager
def prepared_pair(before, after):
    sources = [files(Path(before)), files(Path(after))]
    with tempfile.TemporaryDirectory(prefix="intendiff-normalize-") as temporary:
        directory = Path(temporary)
        roots = [directory / "a", directory / "b"]
        for root in roots:
            root.mkdir()
        jobs, reports = [], []
        identical = 0
        for name in sorted(set(sources[0]) | set(sources[1])):
            paths = [source.get(name) for source in sources]
            if all(paths) and digest(paths[0]) == digest(paths[1]):
                identical += 1
                continue
            for path, root in zip(paths, roots):
                if path is not None:
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
            if not (name.endswith("js") or name.endswith(".ts")):
                continue
            if any(path and path.stat().st_size > MAX_SOURCE_BYTES for path in paths):
                reports.append({"path": name, "status": "raw_fallback", "error": "source_size_limit"})
                continue
            try:
                contents = [path.read_text(encoding="utf-8") if path else None for path in paths]
            except UnicodeDecodeError:
                reports.append({"path": name, "status": "raw_fallback", "error": "non_utf8_source"})
                continue
            jobs.append({"path": name, "before": contents[0], "after": contents[1]})
        for row in normalize_jobs(jobs, directory) if jobs else []:
            for side, root in zip(("before", "after"), roots):
                if row[side] is not None:
                    (root / row["path"]).write_text(row[side], encoding="utf-8")
            reports.append({k: v for k, v in row.items() if k not in ("before", "after")})
        yield roots[0], roots[1], {
            "version": VERSION, "identical_files_skipped": identical,
            "files": sorted(reports, key=lambda r: r["path"]),
            "fallback_files": sum(r["status"] == "raw_fallback" for r in reports),
        }


def selfcheck():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for side in ("a", "b"):
            (root / side).mkdir()
            (root / side / "same.js").write_text("untouched()")
            (root / side / "README.md").write_text(side)
        (root / "b/new.js").write_text("newCode()")
        original = digest(root / "b/new.js")
        def transform(jobs, directory):
            return [dict(j, after="normalized()", status="transformed") for j in jobs]
        with patch(__name__ + ".normalize_jobs", transform):
            with prepared_pair(root / "a", root / "b") as (before, after, report):
                assert not (before / "same.js").exists()
                assert not (after / "README.md").exists()
                assert (after / "new.js").read_text() == "normalized()"
                assert report["identical_files_skipped"] == 1
        assert digest(root / "b/new.js") == original
        assert not after.exists()
        from types import SimpleNamespace
        executable = root / "engine"
        executable.write_text("pinned engine")
        calls = []
        def invoke(command, **kwargs):
            jobs = json.loads(Path(command[1]).read_text())
            calls.append(jobs)
            return SimpleNamespace(stdout=json.dumps([dict(j, status="transformed") for j in jobs]))
        with patch.dict(os.environ, {"INTENDIFF_NORMALIZE_CACHE": str(root / "cache")}), \
             patch("shutil.which", return_value=str(executable)), \
             patch("subprocess.run", invoke):
            job = {"path": "first.js", "before": None, "after": "same code"}
            normalize_jobs([job], root)
            cached = normalize_jobs([dict(job, path="relocated.js")], root)
            assert len(calls) == 1 and cached[0]["path"] == "relocated.js"
            normalize_jobs([dict(job, after="changed code")], root)
            assert len(calls) == 2
    print("isolated normalization selfcheck passed")


if __name__ == "__main__":
    selfcheck()
