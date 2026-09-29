import json

from pipeline.datasets.pairs import build_row
from pipeline.features.files import has_content, package_root
from pipeline.shared.hashing import tree_digest
from pipeline.tests.fixtures import build_fixture, temp_dir, words


def test_package_root_reads_through_the_tarball_wrapper_only():
    root = temp_dir()
    wrapped = build_fixture(root / "wrapped/package", {"package.json": '{"name":"w"}'}).parent
    flat = build_fixture(root / "flat", {"package.json": '{"name":"f"}'})
    assert package_root(wrapped) == wrapped / "package" and package_root(flat) == flat
    assert not has_content(root / "nothing") and has_content(flat)


def test_a_row_takes_its_intent_from_the_previous_version():
    root = temp_dir()
    before = build_fixture(root / "v1", {"package.json": '{"name":"p","version":"1","description":"A tiny helper"}',
                                         "index.js": "module.exports = 1;\n"})
    after = build_fixture(root / "v2", {"package.json": '{"name":"p","version":"2","scripts":{"preinstall":"node s.js"}}',
                                        "index.js": "module.exports = 1;\n",
                                        "s.js": "require('https').request({host:'x.example'});\n"})
    row = build_row("p", "1", "2", before, after, "MAL", "test", words)
    assert row["id"] == "p@2" and row["label"] == "malicious"
    assert "install_script" in row["delta"] and "network" in row["delta"]
    assert row["intent_from"] == "1" and row["intent_available"]
    assert "preinstall" not in json.dumps(row["intent"])
    assert "s.js" in row["diff"] and row["gold_evidence"] == []
    assert row["sha256_before"] == tree_digest(before) != row["sha256_after"]
