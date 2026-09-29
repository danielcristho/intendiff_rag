"""Settings from the environment and the repository's .env, and the layout of the data directory."""
import os
from dataclasses import dataclass
from pathlib import Path

ENV_FILE = Path(".env")
WYSS_PACKAGE = "wyss/package/replication_package_evaluating_llm_mal_update_detection"


def read_env_file(path=ENV_FILE):
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


# setting prefers the process environment over .env, the way docker compose does.
def setting(key, env_file=ENV_FILE):
    value = os.environ.get(key) or read_env_file(env_file).get(key)
    if not value:
        raise SystemExit(f"{key} is not set; add it to .env")
    return value


# Layout names every file the pipeline reads or writes under DATA_DIR.
@dataclass(frozen=True)
class Layout:
    root: Path

    def __truediv__(self, name):
        return self.root / name

    @property
    def pairs(self):
        return self / "pairs.jsonl"

    @property
    def pairs_mal(self):
        return self / "pairs.mal.jsonl"

    @property
    def pairs_typ(self):
        return self / "pairs.typ.jsonl"

    @property
    def pairs_hn(self):
        return self / "pairs.hn.jsonl"

    @property
    def pairs_dev(self):
        return self / "pairs.dev.jsonl"

    @property
    def typ_taken(self):
        return self / "pairs.typ.taken.txt"

    @property
    def dev_taken(self):
        return self / "pairs.dev.taken.txt"

    @property
    def kb_skeleton(self):
        return self / "kb.skeleton.jsonl"

    @property
    def kb_cards(self):
        return self / "kb.cards.json"

    @property
    def kb(self):
        return self / "kb.jsonl"

    @property
    def results(self):
        return self / "results.jsonl"

    @property
    def results_dev(self):
        return self / "results.dev.jsonl"

    @property
    def figures(self):
        return self / "figures"

    @property
    def samples(self):
        return self / "samples.jsonl"

    @property
    def tarballs(self):
        return self / "tarballs"

    @property
    def typ(self):
        return self / "typ"

    @property
    def hn(self):
        return self / "hn"

    @property
    def path_b(self):
        return self / "hn/path-b"

    @property
    def hn_queue(self):
        return self / "hn/queue.jsonl"

    @property
    def datadog(self):
        return self / "datadog"

    @property
    def wyss_listings(self):
        return self / f"{WYSS_PACKAGE}/data"

    @property
    def wyss_mal(self):
        return self / "wyss/samples/m"

    @property
    def wyss_clones(self):
        return self / "wyss/samples/j"


def layout():
    return Layout(Path(setting("DATA_DIR")))


def vllm_url():
    return f"http://localhost:{setting('VLLM_PORT')}"
