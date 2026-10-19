import unittest

from pipeline.evidence import audit_ids, index_diff, render_diff


class EvidenceTests(unittest.TestCase):
    def test_header_like_added_code_is_not_a_file_header(self):
        diff = 'diff -u a/x.js b/x.js\n--- a/x.js\n+++ b/x.js\n@@ -1 +1 @@\n-old\n+++new'
        rows = index_diff(diff)
        self.assertEqual(rows[-1]['kind'], 'added')
        self.assertEqual(rows[-1]['path'], 'x.js')
        self.assertEqual(rows[-1]['new_line'], 1)

    def test_deletions_and_context_retain_distinct_coordinates(self):
        rows = index_diff('@@ -8,2 +20,2 @@\n same\n-old\n+new')
        self.assertEqual((rows[1]['old_line'], rows[1]['new_line']), (8, 20))
        self.assertEqual((rows[2]['old_line'], rows[2]['new_line']), (9, None))
        self.assertEqual((rows[3]['old_line'], rows[3]['new_line']), (None, 21))

    def test_unknown_and_metadata_citations_do_not_prove_behavior(self):
        report = audit_ids('@@ -0,0 +1 @@\n+hello', ['D00001', 'D99999'])
        self.assertEqual(report['unknown_ids'], ['D99999'])
        self.assertEqual(report['content_line_count'], 0)
        self.assertFalse(report['semantic_support_verified'])

    def test_rendering_preserves_every_original_line(self):
        diff = 'diff a/x b/x\n@@ -1 +1 @@\n-old\n+new\n'
        self.assertEqual([line.split('] ', 1)[1] for line in render_diff(diff).splitlines()],
                         diff.splitlines())

    def test_truncated_hunk_does_not_invent_missing_lines(self):
        self.assertEqual(len(index_diff('@@ -0,0 +1,20 @@\n+one')), 2)


if __name__ == '__main__':
    unittest.main()
