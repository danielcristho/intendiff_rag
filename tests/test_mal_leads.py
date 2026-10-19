import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from mal_lead_archives import advisory_gate


class MalLeadTests(unittest.TestCase):
    def setUp(self):
        self.pair = dict(name="pkg", before="1.0.0", after="1.0.1")
        self.before = dict(name="pkg", version="1.0.0", has_advisory=False, advisory_ids=[])
        self.after = dict(name="pkg", version="1.0.1", has_advisory=True, advisory_ids=["MAL-2026-1"])

    def test_source_lead_requires_an_independent_malicious_advisory(self):
        self.assertIsNone(advisory_gate(self.pair, self.before, self.after))
        vulnerability = dict(self.after, advisory_ids=["GHSA-example"])
        self.assertEqual(advisory_gate(self.pair, self.before, vulnerability), "target_has_no_MAL_confirmation")

    def test_malicious_predecessor_is_not_a_clean_baseline(self):
        before = dict(self.before, has_advisory=True, advisory_ids=["MAL-2026-1"])
        self.assertEqual(advisory_gate(self.pair, before, self.after), "predecessor_advisory_present")

    def test_missing_checks_cannot_silently_become_negative(self):
        for check in (None, {}, dict(self.before, error="network error")):
            self.assertEqual(advisory_gate(self.pair, check, self.after), "advisory_check_missing")

    def test_advisory_for_another_version_cannot_supply_a_label(self):
        other = dict(self.after, version="9.0.0")
        self.assertEqual(advisory_gate(self.pair, self.before, other), "advisory_identity_mismatch")


if __name__ == "__main__":
    unittest.main()
