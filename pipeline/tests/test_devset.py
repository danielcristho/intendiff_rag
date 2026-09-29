import json

from pipeline.datasets.devset import draw_clones, read_clones, unused_typical
from pipeline.tests.fixtures import temp_dir


def test_a_clone_keeps_its_original_before_and_its_directory_after():
    listing = temp_dir() / "clones.txt"
    listing.write_text("j_samples/agent-base/agent-base@7.1.1,j_samples/agent-base/agentbas-7.1.1\n"
                       "j_samples/@scope/x/@scope/x@1.0.0,j_samples/@scope/x/sc-x-1.0.0\n")
    entries = read_clones(listing)
    assert (entries[0]["name"], entries[0]["before"], entries[0]["after"]) == ("agent-base", "7.1.1", "agentbas-7.1.1")
    assert (entries[1]["name"], entries[1]["after"]) == ("@scope/x", "sc-x-1.0.0")
    assert draw_clones(entries, 2) == draw_clones(entries[::-1], 2)


def test_a_typical_test_pair_never_enters_the_dev_set():
    work = temp_dir()
    listing = work / "typ.txt"
    listing.write_text("r/a/a@1.0.0,r/a/a@1.0.1\nr/b/b@2.0.0,r/b/b@2.1.0\n")
    (work / "pairs.typ.jsonl").write_text(json.dumps({"id": "a@1.0.1"}) + "\n")
    assert [e["name"] for e in unused_typical([listing], work / "pairs.typ.jsonl")] == ["b"]
