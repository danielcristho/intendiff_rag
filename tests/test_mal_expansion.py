import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from archive_layers import index
from campaign_extend import extend
from mal_expansion_campaign import proposals_for


class MalExpansionTests(unittest.TestCase):
    def test_new_pair_linked_to_a_d99_addition_inherits_its_exposure(self):
        old = [dict(id="old@1", code_key="a"), dict(id="d99@1", code_key="b")]
        added = [dict(id="new@2", code_key="c")]
        assigned = {"old@1": "old@1", "d99@1": "old@1"}
        campaigns, _ = extend(old, added, assigned, lambda a, b: 1 if b == "b" else 0)
        proposals = proposals_for([dict(id="new@2", name="new")], campaigns, assigned, [])
        self.assertIn("campaign_in_historical_pool", proposals[0]["exclusion_reasons"])

    def test_related_dependency_and_current_test_names_are_blocked(self):
        pairs = [dict(id="dependency@2", name="dependency"), dict(id="test@9", name="test")]
        campaigns = {r["id"]: r["id"] for r in pairs}
        exposure = [dict(name="parent", related_names=["dependency"]), dict(name="test", id="test@1")]
        self.assertTrue(all(r["status"] == "excluded" for r in proposals_for(pairs, campaigns, {}, exposure)))

    def test_cap_counts_campaigns_and_is_independent_of_input_order(self):
        pairs = [dict(id=f"p{i}@2", name=f"p{i}") for i in range(5)]
        campaigns = {r["id"]: "shared" for r in pairs}
        proposals = proposals_for(pairs, campaigns, {}, [])
        self.assertEqual(sum(r["status"] == "candidate_new_holdout" for r in proposals), 3)
        self.assertEqual(proposals, proposals_for(list(reversed(pairs)), campaigns, {}, []))

    def test_archive_inventory_does_not_extract_paths_or_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layer = io.BytesIO()
            with tarfile.open(fileobj=layer, mode="w") as tar:
                for name, payload in [("RO/README.md", b"source metadata"), ("../../escape", b"bad")]:
                    member = tarfile.TarInfo(name)
                    member.size = len(payload)
                    tar.addfile(member, io.BytesIO(payload))
                link = tarfile.TarInfo("RO/link.md")
                link.type = tarfile.SYMTYPE
                link.linkname = "/etc/passwd"
                tar.addfile(link)
            archive = root / "image.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                member = tarfile.TarInfo("example/layer.tar")
                member.size = len(layer.getvalue())
                tar.addfile(member, io.BytesIO(layer.getvalue()))
            index(archive, root / "index")
            records = [json.loads(line) for line in (root / "index/members.jsonl").read_text().splitlines()]
            self.assertEqual(len(records), 3)
            self.assertEqual(sum("metadata" in row for row in records), 1)
            self.assertFalse((root / "RO").exists())


if __name__ == "__main__":
    unittest.main()
