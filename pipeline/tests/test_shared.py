from pathlib import Path

from pipeline.shared.config import Layout, read_env_file
from pipeline.shared.hashing import hash_key, hash_order, name_order, tree_digest
from pipeline.shared.isolation import network_interfaces, require_offline
from pipeline.shared.jsonl import append_jsonl, read_jsonl, write_jsonl
from pipeline.shared.specs import configurations, hn_categories
from pipeline.tests.fixtures import build_fixture, temp_dir


def test_env_file_skips_comments_and_section_headers():
    env = temp_dir() / ".env"
    env.write_text("#! Backend\n## note\nDATA_DIR=./data\n\nVLLM_PORT=8101\n")
    assert read_env_file(env) == {"DATA_DIR": "./data", "VLLM_PORT": "8101"}


def test_layout_names_files_under_the_data_directory():
    data = Layout(Path("data"))
    assert str(data.pairs) == "data/pairs.jsonl" and str(data.tarballs) == "data/tarballs"
    assert str(data.path_b) == "data/hn/path-b"


def test_a_missing_jsonl_file_reads_as_empty_and_blank_lines_are_skipped():
    path = temp_dir() / "rows.jsonl"
    assert read_jsonl(path) == []
    write_jsonl(path, [{"a": 1}])
    append_jsonl(path, {"a": 2})
    path.write_text(path.read_text() + "\n\n")
    assert read_jsonl(path) == [{"a": 1}, {"a": 2}]


def test_hash_order_ignores_the_input_order():
    items = [{"name": n, "version": v} for n, v in (("a", "1.0.0"), ("b", "2.0.0"), ("c", "3.0.0"))]
    assert hash_order(items) == hash_order(list(reversed(items)))
    assert hash_key("a", "1.0.0") != hash_key("a", "1.0.1")
    assert name_order(["b", "a", "b"]) == name_order(["a", "b"])


def test_tree_digest_depends_on_content_not_location():
    one = build_fixture(temp_dir() / "x", {"a.js": "1", "sub/b.js": "2"})
    two = build_fixture(temp_dir() / "y", {"a.js": "1", "sub/b.js": "2"})
    assert tree_digest(one) == tree_digest(two)
    (two / "a.js").write_text("changed")
    assert tree_digest(one) != tree_digest(two)


def test_an_interface_besides_loopback_stops_the_analysis():
    net = temp_dir()
    (net / "lo").mkdir()
    require_offline(net)
    (net / "eth0").mkdir()
    assert network_interfaces(net) == ["eth0"]
    try:
        require_offline(net)
    except SystemExit:
        return
    raise AssertionError("an interface besides lo must stop the analysis")


def test_specs_define_five_categories_and_the_configurations_in_order():
    categories = hn_categories()
    assert set(categories) == {1, 2, 3, 4, 5} and categories[2]["signals"] == {"network"}
    assert "deprecated" in categories[5]["keywords"]
    assert list(configurations()) == ["E0-noint", "E0", "E2", "E3", "E3-k2", "E4", "E4-noint"]
