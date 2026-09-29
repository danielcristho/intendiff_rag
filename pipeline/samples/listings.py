"""The Wyss listing format: one "before_path,after_path" line per update."""
from pathlib import Path


# listing_entry splits "<root>/<name>/<name>@<version>" into name and version.
def listing_entry(path):
    rest = path.split("/", 1)[1]
    cut = rest.rfind("@")
    # The name appears twice, so it is the tail half of what precedes the version.
    repeated, version = rest[:cut], rest[cut + 1:]
    return repeated[-((len(repeated) - 1) // 2):], version


def read_listing(path):
    entries = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        before_path, after_path = line.strip().split(",")
        (name, before), (_, after) = listing_entry(before_path), listing_entry(after_path)
        entries.append({"name": name, "before": before, "after": after,
                        "before_path": before_path, "after_path": after_path})
    return entries


def write_listing(path, entries):
    Path(path).write_text("".join(f"{e['before_path']},{e['after_path']}\n" for e in entries))
