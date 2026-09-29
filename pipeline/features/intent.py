"""Intent profile of a version: description, keywords, scripts and README, packed into a budget."""
import argparse
import json
import re
from pathlib import Path

from pipeline.features.files import read_text
from pipeline.features.manifest import package_json
from pipeline.shared.isolation import require_offline
from pipeline.shared.tokens import approx_counter, qwen_counter

TOTAL_BUDGET = 1_024
HEADLINE_BUDGET = 128
SCRIPTS_BUDGET = 256
MISSING = "not available"
HTML_TAG = re.compile(r"<[^>]+>")
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


# readme_path matches "readme" in any case; packages ship readme.md as often as README.md.
def readme_path(version_dir):
    root = Path(version_dir)
    if not root.is_dir():
        return None
    return next((path for path in sorted(root.iterdir())
                 if path.is_file() and path.name.lower().startswith("readme")), None)


# clean_readme drops badge, image and link-only lines and strips HTML tags.
def clean_readme(text):
    kept = []
    for line in text.split("\n"):
        if MARKDOWN_IMAGE.search(line):
            continue
        without_tags = HTML_TAG.sub("", line)
        if without_tags.strip() and not MARKDOWN_LINK.sub("", without_tags).strip():
            continue
        kept.append(without_tags)
    return "\n".join(kept).strip()


# fit cuts text to a token budget by binary search, since tokens are not linear in characters.
def fit(text, budget, count):
    if not text or budget <= 0:
        return ""
    if count(text) <= budget:
        return text
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
    keywords = ", ".join(str(word) for word in keywords) if isinstance(keywords, list) and keywords else MISSING
    return str(description).strip(), str(keywords).strip()


def scripts_block(manifest):
    scripts = manifest.get("scripts")
    if not isinstance(scripts, dict) or not scripts:
        return MISSING
    return "\n".join(f"{name}: {command}" for name, command in scripts.items())


# build packs one version's profile; the README takes whatever budget the other sections left.
def build(version_dir, count, total_budget=TOTAL_BUDGET):
    manifest = package_json(version_dir)
    description, keywords = headline(manifest)
    readme_file = readme_path(version_dir)
    readme_raw = clean_readme(read_text(readme_file) or "") if readme_file else ""
    description = fit(description, HEADLINE_BUDGET, count)
    keywords = fit(keywords, max(HEADLINE_BUDGET - count(description), 0), count)
    scripts = fit(scripts_block(manifest), SCRIPTS_BUDGET, count)
    spent = count(description) + count(keywords) + count(scripts)
    readme = fit(readme_raw, total_budget - spent, count) or MISSING
    return {"description": description or MISSING, "keywords": keywords or MISSING,
            "scripts": scripts or MISSING, "readme": readme}


# available reports whether the profile states a purpose; scripts and keywords alone do not.
def available(profile):
    return profile["description"] != MISSING or profile["readme"] != MISSING


def main(argv=None):
    parser = argparse.ArgumentParser(prog="intent")
    parser.add_argument("--version", required=True, help="the previous version's directory")
    parser.add_argument("--approx", action="store_true", help="count 4 characters per token")
    args = parser.parse_args(argv)
    require_offline()
    profile = build(args.version, approx_counter if args.approx else qwen_counter())
    print(json.dumps({"intent": profile, "intent_available": available(profile)},
                     ensure_ascii=False, indent=2))
