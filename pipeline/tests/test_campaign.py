from pipeline.features.campaign import added_code, added_files, added_hashes, cluster, count_clusters, dolos_similarity
from pipeline.shared.hashing import sha256_text
from pipeline.tests.fixtures import build_fixture, temp_dir


def item(identifier, reports=(), hashes=(), code=""):
    return {"id": identifier, "reports": list(reports), "added_hashes": list(hashes), "code": code}


def groups(assigned):
    return {frozenset(k for k, v in assigned.items() if v == root) for root in set(assigned.values())}


def test_a_shared_report_or_one_identical_file_merges_two_items():
    assert groups(cluster([item("p1", ["R1"]), item("p2", ["R1"]), item("p3", ["R9"])])) == \
        {frozenset({"p1", "p2"}), frozenset({"p3"})}
    shared = sha256_text("payload")
    assert groups(cluster([item("p1", hashes=[shared, "x"]), item("p2", hashes=["y", shared]), item("p3", hashes=["z"])])) \
        == {frozenset({"p1", "p2"}), frozenset({"p3"})}


def test_similarity_merges_at_the_threshold_and_not_below():
    pair = [item("a", code="A"), item("b", code="B")]
    assert groups(cluster(pair, lambda *_: 0.5)) == {frozenset({"a", "b"})}
    assert groups(cluster(pair, lambda *_: 0.49)) == {frozenset({"a"}), frozenset({"b"})}


def test_links_close_transitively_and_the_label_is_the_smallest_id():
    chain = [item("p1", ["R"]), item("p2", ["R"], code="B"), item("p3", code="C")]
    assert groups(cluster(chain, lambda a, b: 0.9 if {a, b} == {"B", "C"} else 0.0)) == {frozenset({"p1", "p2", "p3"})}
    assert cluster([item("zz", ["R"]), item("aa", ["R"])]) == cluster([item("aa", ["R"]), item("zz", ["R"])]) \
        == {"zz": "aa", "aa": "aa"}


def test_a_stricter_threshold_never_merges_more():
    graded = {("A", "B"): 0.6, ("A", "C"): 0.9, ("B", "C"): 0.2}
    counts = count_clusters([item("p1", code="A"), item("p2", code="B"), item("p3", code="C")],
                            lambda a, b: graded.get((a, b)) or graded.get((b, a)) or 0.0)
    assert counts == {0.5: 1, 0.8: 2}


def test_added_files_skip_unchanged_ones_and_code_keeps_javascript_only():
    root = temp_dir()
    before = build_fixture(root / "v1", {"src/index.js": "shared();"})
    after = build_fixture(root / "v2", {"src/index.js": "shared();", "src/payload.js": "exfiltrate();",
                                        "notes.txt": "not javascript"})
    assert set(added_files(before, after)) == {"src/payload.js", "notes.txt"}
    code = added_code(before, after)
    assert "exfiltrate()" in code and "shared()" not in code and "not javascript" not in code
    assert sha256_text("exfiltrate();") in added_hashes(before, after)
    assert dolos_similarity("", "anything") == 0.0
