import json

from pipeline.datasets.hn import path_b, rules
from pipeline.datasets.hn.path_a import screen
from pipeline.datasets.hn.queue import queue_order
from pipeline.samples import registry
from pipeline.tests.fixtures import build_fixture, temp_dir

DOC = {"versions": {v: {"dist": {"tarball": "t"}, "_npmUser": {"name": "alice"}}
                    for v in ("1.0.0", "1.0.1", "1.0.2", "1.0.3")}, "time": {}}
DELTAS = {"1.0.1": ["dependency_change"], "1.0.2": ["network"], "1.0.3": ["network"]}


def test_categories_follow_the_signals_and_reasons_group_by_kind():
    assert rules.matching_categories(["network"]) == [2, 4] and rules.matching_categories([]) == []
    assert rules.matching_categories(["network", "process_exec"]) == [1, 2, 4]
    assert rules.reason_kind("publisher a -> b") == rules.reason_kind("publisher c -> d") == "publisher"


def test_an_advisory_on_the_old_version_leaves_the_update_eligible():
    real = registry.has_advisory
    registry.has_advisory = lambda name, version, **_: version == "1.0.0"
    try:
        doc = {"versions": {"1.0.0": {}, "1.0.1": {}}}
        assert rules.hn_rejection(doc, "fix", "1.0.0", "1.0.1") is None
        assert rules.hn_rejection(doc, "bad", "0.9.0", "1.0.0") == "advisory"
    finally:
        registry.has_advisory = real


def test_screen_reports_an_unextracted_pair_instead_of_an_empty_delta():
    out = temp_dir()
    build_fixture(out / "b/p/p@1.0.0", {"index.js": "module.exports = 1;", "package.json": '{"name": "p"}'})
    build_fixture(out / "b/p/p@1.0.1", {"index.js": "require('https').get('x');", "package.json": '{"name": "p"}'})
    entry = {"name": "p", "before": "1.0.0", "after": "1.0.1", "publisher": "alice",
             "before_path": "b/p/p@1.0.0", "after_path": "b/p/p@1.0.1"}
    kept, reasons = screen([entry, {**entry, "after": "2.0.0", "after_path": "b/p/p@2.0.0"}], out)
    assert kept[0]["delta"] == ["network"] and kept[0]["categories"] == [2, 4] and kept[0]["publisher"] == "alice"
    assert reasons == [("p@2.0.0", "not extracted")]


def with_stubbed_delta(check):
    out = temp_dir()
    path_b.packument_path(out, "demo").parent.mkdir(parents=True)
    path_b.packument_path(out, "demo").write_text(json.dumps(DOC))
    real = (path_b.pair_delta, path_b.hn_rejection)
    path_b.pair_delta = lambda entry, _out: (DELTAS.get(entry["after"], []), None)
    try:
        check(out)
    finally:
        path_b.pair_delta, path_b.hn_rejection = real


def test_path_b_takes_the_earliest_matching_pair_and_does_not_shop_for_a_later_one():
    def check(out):
        matches, _ = path_b.match_category(2, ["demo"], out)
        assert matches[0]["entry"]["after"] == "1.0.2"
        assert path_b.match_category(5, ["demo"], out)[0][0]["entry"]["after"] == "1.0.1"
        path_b.hn_rejection = lambda _doc, _name, _before, after: "advisory" if after == "1.0.2" else None
        assert path_b.verify(2, matches, out, 5, set()) == ([], [("demo@1.0.2", "advisory")])
        path_b.hn_rejection = lambda *_: None
        kept, _ = path_b.verify(2, matches, out, 5, set())
        assert kept[0]["source"] == "path-b" and kept[0]["publisher"] == "alice"
        assert path_b.verify(2, matches, out, 5, {"demo@1.0.2"})[0] == []

    with_stubbed_delta(check)


def test_the_packument_keeps_only_what_the_match_and_verify_read():
    assert path_b.slim_packument({**DOC, "readme": "x" * 1000}) == DOC
    assert path_b.name_order(["b", "a", "b"]) == path_b.name_order(["a", "b"])


def test_the_queue_puts_path_a_first_and_lists_a_pair_once():
    a = [{"name": "x", "after": "1.0.1"}, {"name": "y", "after": "2.0.0"}]
    b = [{"name": "z", "after": "3.0.0"}, {"name": "x", "after": "1.0.1"}]
    order = queue_order(a, b)
    assert [source for source, _ in order] == ["path-a", "path-a", "path-b"]
    assert queue_order(list(reversed(a)), []) == queue_order(a, [])
