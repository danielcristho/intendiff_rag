"""SHA-256 digests and the hash order every selection follows."""
import hashlib
from pathlib import Path


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_key(name, version):
    return sha256_text(f"{name}@{version}")


# hash_order sorts by the digest of name@version, which popularity or listing order cannot steer.
def hash_order(items, key=lambda item: (item["name"], item["version"])):
    return sorted(items, key=lambda item: hash_key(*key(item)))


# name_order sorts package names by digest and drops repeats.
def name_order(names):
    return sorted(dict.fromkeys(names), key=sha256_text)


# tree_digest hashes a directory as sorted "path\0sha256" lines, independent of where it sits.
def tree_digest(root):
    root = Path(root)
    lines = [f"{path.relative_to(root).as_posix()}\0{sha256_file(path)}"
             for path in sorted(root.rglob("*")) if path.is_file()]
    return sha256_text("\n".join(lines))
