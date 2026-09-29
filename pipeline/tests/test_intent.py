import json

from pipeline.features.intent import (HEADLINE_BUDGET, MISSING, SCRIPTS_BUDGET, TOTAL_BUDGET, available, build,
                                      clean_readme, fit)
from pipeline.tests.fixtures import Versions, words

version = Versions()


def test_readme_cleaning_drops_badges_tags_and_link_only_lines():
    readme = clean_readme("# tinylint\n[![build](https://img.shields.io/x.svg)](https://ci.example)\n"
                          "<p align=\"center\">A minimal linter.</p>\n\nLints your files.\n")
    assert "img.shields.io" not in readme and "<p align" not in readme
    assert "A minimal linter." in readme and "Lints your files." in readme
    assert clean_readme("[docs](https://example.com)") == ""
    assert "See the" in clean_readme("See the [docs](https://example.com) for more.")


def test_a_complete_profile_carries_every_section():
    profile = build(version({"package.json": json.dumps({"description": "Minimal linter", "keywords": ["lint", "style"],
                                                         "scripts": {"test": "jest", "build": "tsc"}}),
                             "README.md": "# tinylint\n\nLints your files without a config.\n"}), words)
    assert profile["description"] == "Minimal linter" and profile["keywords"] == "lint, style"
    assert "test: jest" in profile["scripts"] and "without a config" in profile["readme"] and available(profile)


def test_missing_fields_are_stated_and_scripts_alone_state_no_purpose():
    thin = build(version({"package.json": "{}"}), words)
    assert all(thin[field] == MISSING for field in ("description", "keywords", "scripts", "readme"))
    assert not available(thin)
    assert not available(build(version({"package.json": json.dumps({"scripts": {"test": "jest"}})}), words))
    assert available(build(version({"README.md": "Formats JavaScript files."}), words))


def test_the_readme_absorbs_the_slack_and_no_section_overruns():
    long_readme = "word " * 4_000
    quiet = build(version({"package.json": "{}", "README.md": long_readme}), words)
    busy = build(version({"package.json": json.dumps({"description": "d " * 60,
                                                      "scripts": {f"s{i}": "cmd " * 10 for i in range(40)}}),
                          "README.md": long_readme}), words)
    assert words(quiet["readme"]) > words(busy["readme"])
    for profile in (quiet, busy):
        assert sum(words(profile[field]) for field in profile) <= TOTAL_BUDGET
    assert words(busy["scripts"]) <= SCRIPTS_BUDGET and words(busy["description"]) <= HEADLINE_BUDGET


def test_fit_cuts_on_a_word_boundary_and_readme_is_found_in_any_case():
    assert fit("one two three four", 2, words) == "one two" and fit("anything", 0, words) == ""
    for name in ("README.md", "readme.md", "README", "Readme.markdown"):
        assert available(build(version({name: "Purpose here."}), words)), name
