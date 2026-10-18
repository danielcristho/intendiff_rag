"""Index Docker-export TAR layers as data inside a network-disabled container.

    python pipeline/archive_layers.py --archive FILE --out DIR
"""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath


def index(archive, output):
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    with tarfile.open(archive, "r|gz") as outer, (output / "members.jsonl").open("w") as records:
        for layer in outer:
            if not layer.isfile() or not layer.name.endswith("/layer.tar"):
                continue
            with tarfile.open(fileobj=outer.extractfile(layer), mode="r|") as inner:
                for member in inner:
                    count += 1
                    if count > 2_000_000:
                        raise ValueError("member count exceeds inventory limit")
                    row = {"layer": layer.name, "path": member.name,
                           "bytes": member.size, "type": member.type.decode("ascii", "replace")}
                    parts = PurePosixPath(member.name).parts
                    if (member.isfile() and parts and parts[0] == "RO"
                            and "node_modules" not in parts and ".git" not in parts
                            and member.size <= 2 * 1024**2
                            and Path(member.name).suffix.lower() in (".csv", ".md") ):
                        payload = inner.extractfile(member).read()
                        digest = hashlib.sha256(payload).hexdigest()
                        target = output / "metadata" / (digest + Path(member.name).suffix.lower())
                        target.parent.mkdir(exist_ok=True)
                        target.write_bytes(payload)
                        row.update(metadata=str(target), sha256=digest)
                    records.write(json.dumps(row) + "\n")
            records.flush()
            print(json.dumps({"layer": layer.name, "members": count}), flush=True)
    (output / "summary.json").write_text(json.dumps({"members": count, "archive": str(archive)}) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    index(args.archive, args.out)
