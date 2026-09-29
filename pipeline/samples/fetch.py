"""Download npm tarballs on the host and record their SHA-256 for the offline steps."""
import hashlib
import urllib.request
from pathlib import Path

from pipeline.samples.extract import plan_row
from pipeline.samples.registry import matches_integrity, tarball_url
from pipeline.shared.jsonl import append_jsonl, read_jsonl


def download(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


# Fetcher keeps the tarball store and its checksum log in step.
class Fetcher:
    def __init__(self, layout, get=download):
        self.root, self.samples, self.get = Path(layout.tarballs), Path(layout.samples), get
        self.known = {(row["name"], row["version"]): row["sha256"] for row in read_jsonl(self.samples)}

    def path(self, name, version):
        return self.root / name / f"{version}.tgz"

    # fetch returns (path, sha256) for one version, or (None, reason).
    def fetch(self, doc, name, version):
        url = tarball_url(doc, version)
        if not url:
            return None, "unpublished"
        path = self.path(name, version)
        if path.is_file() and (name, version) in self.known:
            return path, self.known[(name, version)]
        try:
            payload = self.get(url)
        except Exception as exc:  # noqa: BLE001 - any failure means "no sample"
            return None, f"{type(exc).__name__}: {exc}"
        # A download that disagrees with the registry once left a wrong checksum in samples.jsonl.
        if not matches_integrity(doc, version, payload):
            return None, "integrity mismatch"
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(".part")
        partial.write_bytes(payload)
        partial.rename(path)
        sha = hashlib.sha256(payload).hexdigest()
        append_jsonl(self.samples, {"name": name, "version": version, "url": url,
                                    "sha256": sha, "bytes": len(payload)})
        self.known[(name, version)] = sha
        return path, sha

    # plan fetches both sides of an entry and returns (plan rows, None) or (None, reason).
    def plan(self, doc, entry, out):
        rows = []
        for side, version in (("before_path", entry["before"]), ("after_path", entry["after"])):
            path, sha = self.fetch(doc, entry["name"], version)
            if path is None:
                return None, sha
            rows.append(plan_row(path, Path(out) / entry[side], sha))
        return rows, None
