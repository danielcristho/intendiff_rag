import shutil

from pipeline.features.smartdiff import build, fit_budget, order_files, signals_per_file
from pipeline.features.unified_diff import raw_diff, relabel_paths, split_by_file, split_hunks, truncate_long_lines
from pipeline.tests.fixtures import build_fixture, temp_dir, words


def pair():
    root = temp_dir()
    shared = {"README.md": "prose\n", "LICENSE": "prose\n", "yarn.lock": "prose\n"}
    before = build_fixture(root / "v1", {**shared, "package.json": '{"name":"p","version":"1"}',
                                         "src/index.js": "module.exports = 1;\n",
                                         "logo.png": b"\x89PNG\r\n\x1a\n\x00\x01"})
    after = build_fixture(root / "v2", {"README.md": "new prose\n", "LICENSE": "new prose\n",
                                        "yarn.lock": "new prose\n", "package.json": '{"name":"p","version":"2"}',
                                        "src/index.js": "module.exports = 2;\n",
                                        "src/setup.js": "require('https');\nprocess.env;\n",
                                        "logo.png": b"\x89PNG\r\n\x1a\n\x00\xff"})
    return root, before, after


def test_a_long_line_is_capped_and_says_how_much_was_dropped():
    capped = truncate_long_lines("x" * 2500, limit=2000)
    assert capped.startswith("x" * 2000) and capped.endswith("…[+500 chars]")
    assert truncate_long_lines("a\nb") == "a\nb"


def test_the_diff_excludes_prose_keeps_binaries_and_hides_the_extraction_path():
    root, before, after = pair()
    text = relabel_paths(raw_diff(before, after), before, after)
    assert "setup.js" in text and "require('https')" in text and "-module.exports = 1;" in text
    assert "README" not in text and "new prose" not in text and "LICENSE" not in text and "yarn.lock" not in text
    assert "Binary files" in text and str(root) not in text
    assert "--- a/package.json" in text and "+++ b/package.json" in text


def test_the_same_pair_gives_the_same_text_wherever_it_was_unpacked():
    root, before, after = pair()
    text = relabel_paths(raw_diff(before, after), before, after)
    shutil.copytree(before, root / "moved/A")
    shutil.copytree(after, root / "moved/B")
    assert relabel_paths(raw_diff(root / "moved/A", root / "moved/B"), root / "moved/A", root / "moved/B") == text


def test_quoted_names_lose_their_timestamp_and_sections_follow_byte_order():
    root = temp_dir()
    for side, body in (("A", "1"), ("B", "2")):
        build_fixture(root / side, {name: body + "\n" for name in ("a.js", "B.js", "_x.js", "has space.js")})
    text = relabel_paths(raw_diff(root / "A", root / "B"), root / "A", root / "B")
    assert '--- "a/has space.js"\n' in text
    order = [line.split(" b/")[-1] for line in text.splitlines() if line.startswith("diff ")]
    assert order == sorted(order, key=lambda name: name.strip('"').encode())


def test_package_json_comes_first_then_files_with_more_signals():
    _, before, after = pair()
    chunks = split_by_file(relabel_paths(raw_diff(before, after), before, after), after_root="b")
    assert {"package.json", "src/index.js", "src/setup.js", "logo.png"} <= {c["path"] for c in chunks}
    signals = signals_per_file(after)
    ordered = [chunk["path"] for chunk in order_files(chunks, signals)]
    assert ordered[0] == "package.json" and ordered.index("src/setup.js") < ordered.index("logo.png")
    assert not fit_budget(order_files(chunks, signals), words, budget=10_000)[1]
    assert "files omitted" in fit_budget(order_files(chunks, signals), words, budget=0)[0]


def test_a_file_too_large_for_the_budget_is_cut_between_hunks():
    many = "diff -N -U 0 -r a/big.js b/big.js\n--- a/big.js\n+++ b/big.js\n" + "".join(
        f"@@ -{i},1 +{i},1 @@\n-old line {i}\n+new line {i}\n" for i in range(20))
    header, hunks = split_hunks(many)
    assert len(hunks) == 20
    partial, truncated = fit_budget([{"path": "big.js", "text": many}], words,
                                    budget=words(header) + words(hunks[0]) * 3)
    assert truncated and partial.count("@@ ") == 3
    assert "+new line 2" in partial and "+new line 3" not in partial


def test_build_reports_truncation_and_keeps_the_manifest_first():
    _, before, after = pair()
    result = build(before, after, words, budget=10_000)
    assert result["truncated"] is False and result["diff"].index("package.json") < result["diff"].index("setup.js")
    assert build(before, after, words, budget=1)["truncated"] is True
