"""The Datadog malicious-intent samples: the pool order, fetching zips, and their package roots."""
import json
import subprocess

from pipeline.features.files import package_root
from pipeline.samples.extract import plan_row
from pipeline.shared.hashing import hash_key

SAMPLE_DIR = "samples/npm/malicious_intent"
ZIP_PASSWORD = "infected"  # published in the Datadog dataset README
MAX_UNPACKED = 50 * 2**20


# NotFetched stops the selection when it reaches a sample the host has not fetched yet.
class NotFetched(Exception):
    pass


# pool lists every malicious-intent npm sample in hash order; a null manifest entry marks intent.
def pool(datadog):
    manifest = json.loads((datadog / "samples/npm/manifest.json").read_text())
    tree = subprocess.run(["git", "-C", str(datadog), "ls-tree", "-r", "--name-only", "HEAD", SAMPLE_DIR],
                          capture_output=True, text=True, check=True).stdout.split()
    entries = []
    for path in tree:
        # <name...>/<version>/<file>.zip, where a scoped name carries one extra segment.
        parts = path[len(SAMPLE_DIR) + 1:].split("/")
        name, version = "/".join(parts[:-2]), parts[-2]
        if name in manifest and manifest[name] is None:
            entries.append({"name": name, "version": version, "path": path})
    return sorted(entries, key=lambda entry: hash_key(entry["name"], entry["version"]))


def sample_key(entry):
    return f"{entry['name'].replace('/', '__')}@{entry['version']}"


# fetch_samples writes the first `count` pool zips from the blobless clone and plans their unpacking.
def fetch_samples(datadog, entries, count):
    zips, cache, plan = datadog / "zips", datadog / "extracted", []
    zips.mkdir(parents=True, exist_ok=True)
    for entry in entries[:count]:
        archive = zips / f"{sample_key(entry)}.zip"
        if not archive.exists():
            blob = subprocess.run(["git", "-C", str(datadog), "show", f"HEAD:{entry['path']}"],
                                  capture_output=True, check=True).stdout
            archive.write_bytes(blob)
        plan.append(plan_row(archive, cache / sample_key(entry), password=ZIP_PASSWORD, max_bytes=MAX_UNPACKED))
    return plan


# manifest_root is the shallowest package.json directory, below Datadog's tmp/<random>/<name>/ wrapper.
def manifest_root(extracted):
    manifests = [path for path in extracted.rglob("package.json") if "node_modules" not in path.parts]
    if not manifests:
        return None
    return package_root(min(manifests, key=lambda path: (len(path.parts), str(path))).parent)


# extracted_root returns a fetched sample's package root, None when unreadable.
def extracted_root(datadog, entry):
    target = datadog / "extracted" / sample_key(entry)
    if not target.exists():
        raise NotFetched(sample_key(entry))
    return manifest_root(target)
