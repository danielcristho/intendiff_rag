"""Intent profile builder.

    python pipeline/intent.py --version DIR [--approx]
    python pipeline/intent.py --selfcheck
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from capability import package_json, read_text  # noqa: E402

TOTAL_BUDGET = 1_024
HEADLINE_BUDGET = 128
SCRIPTS_BUDGET = 256
MISSING = "not available"

HTML_TAG = re.compile(r"<[^>]+>")
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def readme_path(version_dir):
    # Case-insensitive: npm packages ship readme.md lowercase at least as
    # often as README.md, and a case-sensitive glob silently finds neither.
    root = Path(version_dir)
    if not root.is_dir():
        return None
    for path in sorted(root.iterdir()):
        if path.is_file() and path.name.lower().startswith("readme"):
            return path
    return None


# clean_readme drops badge and image lines and strips HTML tags (§4.4).
def clean_readme(text):
    kept = []
    for line in text.split("\n"):
        # A badge line is nothing but images and links.
        if MARKDOWN_IMAGE.search(line):
            continue
        without_tags = HTML_TAG.sub("", line)
        # Strip the whole link, label included: keeping the label would let
        # every link-only line through, since the label is itself text.
        if without_tags.strip() and not MARKDOWN_LINK.sub("", without_tags).strip():
            continue
        kept.append(without_tags)
    return "\n".join(kept).strip()


# Cuts on a word boundary, never mid-token.
def fit(text, budget, count):
    if not text or budget <= 0:
        return ""
    if count(text) <= budget:
        return text
    # Binary search: tokens are not linear in characters, so a ratio overshoots.
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if count(text[:middle]) <= budget:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip()


def headline(manifest):
    description = manifest.get("description") or MISSING
    keywords = manifest.get("keywords")
    if isinstance(keywords, list) and keywords:
        keywords = ", ".join(str(word) for word in keywords)
    else:
        keywords = MISSING
    return str(description).strip(), str(keywords).strip()


# §4.4 wants one "name: command" line per script.
def scripts_block(manifest):
    scripts = manifest.get("scripts")
    if not isinstance(scripts, dict) or not scripts:
        return MISSING
    return "\n".join(f"{name}: {command}" for name, command in scripts.items())


# build returns the intent profile of one version, packed into §4.4's budget.
def build(version_dir, count, total_budget=TOTAL_BUDGET):
    manifest = package_json(version_dir)
    description, keywords = headline(manifest)
    scripts = scripts_block(manifest)

    readme_file = readme_path(version_dir)
    readme_raw = clean_readme(read_text(readme_file) or "") if readme_file else ""

    description = fit(description, HEADLINE_BUDGET, count)
    keywords = fit(keywords, max(HEADLINE_BUDGET - count(description), 0), count)
    scripts = fit(scripts, SCRIPTS_BUDGET, count)

    # The README takes whatever the other sections left, not a fixed slice.
    spent = count(description) + count(keywords) + count(scripts)
    readme = fit(readme_raw, total_budget - spent, count) or MISSING

    return {
        "description": description or MISSING,
        "keywords": keywords or MISSING,
        "scripts": scripts or MISSING,
        "readme": readme,
    }


def available(profile):
    # Scripts and keywords alone do not state a purpose.
    return profile["description"] != MISSING or profile["readme"] != MISSING


# §4.4 budgets in Qwen2.5-Coder-3B tokens.
def qwen_counter(model="Qwen/Qwen2.5-Coder-3B-Instruct"):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - depends on the host
        raise RuntimeError(
            "§4.4 budgets in Qwen2.5-Coder-3B tokens; install transformers, "
            "or pass a counter explicitly for tests"
        ) from exc
    tokenizer = AutoTokenizer.from_pretrained(model)
    return lambda text: len(tokenizer(text)["input_ids"])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="the v_(t-1) directory")
    parser.add_argument("--approx", action="store_true",
                        help="count 4 characters per token instead of loading the tokenizer")
    args = parser.parse_args(argv)

    count = (lambda text: len(text) // 4) if args.approx else qwen_counter()
    profile = build(args.version, count)
    print(json.dumps({"intent": profile, "intent_available": available(profile)},
                     ensure_ascii=False, indent=2))


def selfcheck():
    import tempfile

    words = lambda text: len(text.split())  # noqa: E731 - deterministic stand-in
    tmp = Path(tempfile.mkdtemp())
    seq = [0]

    def version(files):
        seq[0] += 1
        root = tmp / f"v{seq[0]}"
        root.mkdir()
        for name, content in files.items():
            (root / name).write_text(content, encoding="utf-8")
        return root

    # --- badge and image lines go, prose stays (§4.4)
    readme = clean_readme(
        "# tinylint\n"
        "[![build](https://img.shields.io/x.svg)](https://ci.example)\n"
        "[![npm](https://img.shields.io/y.svg)](https://npm.example)\n"
        "<p align=\"center\">A minimal linter.</p>\n"
        "\n"
        "Lints your files.\n"
    )
    assert "img.shields.io" not in readme, readme
    assert "<p align" not in readme, readme
    assert "A minimal linter." in readme and "Lints your files." in readme, readme
    # A line that is only a link carries no purpose either.
    assert clean_readme("[docs](https://example.com)") == "", clean_readme("[docs](https://example.com)")
    # But a link inside a sentence keeps the sentence.
    assert "See the" in clean_readme("See the [docs](https://example.com) for more.")

    # --- a complete profile
    full = version({
        "package.json": json.dumps({
            "description": "Minimal linter",
            "keywords": ["lint", "style"],
            "scripts": {"test": "jest", "build": "tsc"},
        }),
        "README.md": "# tinylint\n\nLints your files without a config.\n",
    })
    profile = build(full, words)
    assert profile["description"] == "Minimal linter"
    assert profile["keywords"] == "lint, style"
    assert "test: jest" in profile["scripts"] and "build: tsc" in profile["scripts"]
    assert "without a config" in profile["readme"]
    assert available(profile)

    # --- missing fields are stated, not silently dropped
    bare = version({"package.json": "{}"})
    thin = build(bare, words)
    assert all(thin[field] == MISSING for field in ("description", "keywords", "scripts", "readme"))
    # No description and no README means the pair is flagged, but still included.
    assert not available(thin)

    # Scripts alone do not amount to a statement of purpose.
    scripted = version({"package.json": json.dumps({"scripts": {"test": "jest"}})})
    assert not available(build(scripted, words))
    # A README alone does.
    documented = version({"README.md": "Formats JavaScript files."})
    assert available(build(documented, words))

    # --- README takes what the other sections leave, not a fixed slice
    long_readme = "word " * 4_000
    quiet = version({"package.json": "{}", "README.md": long_readme})
    busy = version({
        "package.json": json.dumps({
            "description": "d " * 60,
            "scripts": {f"s{i}": "cmd " * 10 for i in range(40)},
        }),
        "README.md": long_readme,
    })
    quiet_profile, busy_profile = build(quiet, words), build(busy, words)
    assert words(quiet_profile["readme"]) > words(busy_profile["readme"]), "README must absorb the slack"

    # --- the total is what §4.5 depends on; neither version may exceed it
    for profile in (quiet_profile, busy_profile):
        spent = sum(words(profile[field]) for field in profile)
        assert spent <= TOTAL_BUDGET, spent

    # Each section also respects its own cap.
    assert words(busy_profile["scripts"]) <= SCRIPTS_BUDGET
    assert words(busy_profile["description"]) <= HEADLINE_BUDGET

    # --- fit cuts on a word boundary and never overshoots
    assert fit("one two three four", 2, words) == "one two"
    assert fit("short", 99, words) == "short"
    assert fit("", 10, words) == ""
    assert fit("anything", 0, words) == ""

    # --- README found whatever its case; chalk and ms ship it lowercase.
    for name in ("README.md", "readme.md", "README", "Readme.markdown"):
        found = version({name: "Purpose here."})
        assert available(build(found, words)), name

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
