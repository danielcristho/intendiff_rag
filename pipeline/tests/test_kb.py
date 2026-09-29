from pipeline.datasets.kb.cards import SCHEMA, TEXT_FIELDS, card
from pipeline.datasets.kb.datadog import manifest_root
from pipeline.datasets.kb.promote import problems, sample_lines
from pipeline.datasets.kb.select import assign_campaigns, select, skeleton
from pipeline.tests.fixtures import build_fixture, temp_dir, words

SCANS = {"a": {"delta": ["network"], "hashes": {"h1"}, "evidence": {}, "root": "r/a"},
         "b": {"delta": ["network"], "hashes": {"h1"}, "evidence": {}},
         "c": {"delta": ["network"], "hashes": {"h1"}, "evidence": {}},
         "d": {"delta": ["process_exec"], "hashes": {"mal"}, "evidence": {}},
         "e": {"delta": ["process_exec", "network"], "hashes": {"h2"}, "evidence": {}},
         "f": None}


def chosen():
    entries = [{"name": name, "version": "1.0.0", "path": ""} for name in "fabcde"]
    return select(entries, lambda e: SCANS[e["name"]], {"mal"}, total=4, log=lambda _: None)


def test_a_campaign_never_gives_a_third_card_and_a_test_campaign_gives_none():
    cards, skipped = chosen()
    names = [c["entry"]["name"] for c in cards]
    assert names.count("a") + names.count("b") + names.count("c") == 2 and skipped["campaign_full"] >= 1
    assert "d" not in names and skipped["mal_campaign"] >= 1 and skipped["unreadable"] >= 1


def test_selection_rotates_capabilities_and_takes_each_sample_once():
    cards, _ = chosen()
    names = [c["entry"]["name"] for c in cards]
    assert cards[1]["wanted"] == "process_exec" and names[1] == "e" and len(names) == len(set(names))
    labels = assign_campaigns(cards)
    assert labels[cards[0]["id"]] == labels[cards[2]["id"]]
    row = skeleton(cards[0], "c1")
    assert all(row[field] == "" for field in TEXT_FIELDS) and row["name"] == "a"


def test_the_datadog_wrapper_and_node_modules_are_not_the_package_root():
    work = temp_dir()
    wrapped = build_fixture(work / "tmp/x/pkg/package", {"package.json": "{}", "node_modules/dep/package.json": "{}"})
    build_fixture(work / "tmp/x/pkg", {"package_info-pkg.json": "{}"})
    assert manifest_root(work) == wrapped


def test_only_an_approved_verbatim_card_within_budget_is_promoted():
    root = build_fixture(temp_dir(), {"index.js": "const a = 1;\n  fetch(url);\n"})
    row = {"id": "c", "name": "p", "label": "malicious", "campaign": "c", "source": "datadog",
           "delta": ["network"], "root": str(root), "delta_evidence": {}, "selected_for": "network"}
    good = {"stage": "approved", "intent": "Claims to be a helper.", "behavior_chain": "a -> b",
            "code_excerpt": "fetch(url);", "rationale": "Sends data."}
    assert problems(row, good, words, sample_lines) == []
    assert problems(row, {**good, "stage": "submitted"}, words, sample_lines) and problems(row, None, words, sample_lines)
    assert any("verbatim" in p for p in problems(row, {**good, "code_excerpt": "fetch(evil);"}, words, sample_lines))
    assert any("lines" in p for p in problems(row, {**good, "code_excerpt": "\n".join(["fetch(url);"] * 16)},
                                              words, sample_lines))
    assert any("intent" in p for p in problems(row, {**good, "intent": "w " * 65}, words, sample_lines))
    assert set(card(row, good)) == set(SCHEMA)
