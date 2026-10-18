import hashlib
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from campaign import cluster
from campaign_extend import extend
from external_mal_targets import target_identity
from label_provenance import reference, validate
from source_cards import build, verify
import dataset
from source_budget import chat_tokens


class SourceLabelTests(unittest.TestCase):
    def test_chat_budget_counts_ids_not_batch_encoding_fields(self):
        class Tokenizer:
            def apply_chat_template(self, *args, **kwargs):
                return {'input_ids': list(range(100)), 'attention_mask': [1] * 100}
        self.assertEqual(chat_tokens(Tokenizer(), []), 100)

    def test_unrelated_duplicate_source_ids_do_not_discard_every_card(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.jsonl'
            row = dict(id='p@2', name='p', version='2', source_label='malicious')
            other = dict(id='q@1', name='q', version='1', source_label='malicious')
            path.write_text(''.join(json.dumps(r) + '\n' for r in (row, other, other)))
            entry = dict(row, label='malicious', label_provenance=reference(path, row, 'source_malicious'))
            self.assertIsNone(validate(entry))
            entry = dict(other, label='malicious', label_provenance=reference(path, other, 'source_malicious'))
            self.assertEqual(validate(entry), 'ambiguous_label_source_record')

    def test_preprocessing_preserves_acquisition_hashes_and_label_provenance(self):
        row = dict(id='p@2', name='p', before='1', after='2', before_dir='old', after_dir='new',
                   sha256_before='a', sha256_after='b', label_provenance={'basis': 'source_malicious'})
        with patch.object(dataset.smartdiff, 'build', return_value=dict(diff='+x', truncated=False)), \
             patch.object(dataset.intent_builder, 'build', return_value={'description': 'purpose', 'readme': ''}), \
             patch.object(dataset.capability, 'delta', return_value=[]), \
             patch.object(dataset.capability, 'delta_evidence', return_value={}):
            result = dataset.build_row(row, len)
            self.assertEqual(result['sha256_before'], 'a')
            self.assertEqual(result['sha256_after'], 'b')
            self.assertEqual(result['label_provenance'], row['label_provenance'])
            with self.assertRaisesRegex(ValueError, 'Conflicting archive checksum'):
                dataset.build_row(row, len, {('p', '1'): 'changed'})

    def test_pending_hn_cannot_become_assumed_benign(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.jsonl'
            source = dict(id='p@2', name='p', before='1', after='2', subset='HN', annotation_status='pending')
            path.write_text(json.dumps(source) + '\n')
            row = dict(source, label='benign', label_provenance=reference(path, source, 'assumed_benign'))
            self.assertEqual(validate(row), 'label_not_supported_by_source')

    def test_typical_requires_both_version_checks_and_unchanged_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.jsonl'
            source = dict(id='p@2', name='p', before='1', after='2', subset='TYP', assumed_label='benign',
                          advisory_checks=[dict(name='p', version='2', has_advisory=False)])
            path.write_text(json.dumps(source) + '\n')
            row = dict(source, label='benign', label_provenance=reference(path, source, 'assumed_benign'))
            self.assertEqual(validate(row), 'label_not_supported_by_source')
            source['advisory_checks'].append(dict(name='p', version='1', has_advisory=False))
            path.write_text(json.dumps(source) + '\n')
            self.assertEqual(validate(row), 'label_source_hash_mismatch')
            row['label_provenance'] = reference(path, source, 'assumed_benign')
            self.assertIsNone(validate(row))
            self.assertEqual(validate(dict(row, name='different')), 'label_source_identity_mismatch')

    def test_cards_are_verbatim_source_bound_and_not_human_annotations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'package.json').write_text(json.dumps(dict(name='p', version='2', description='A utility')))
            (root / 'index.js').write_text("const http = require('https');\nhttp.get('https://example.invalid');\n\n\n")
            source = dict(id='p@2', name='p', version='2', source_label='malicious')
            path = root / 'source.jsonl'; path.write_text(json.dumps(source) + '\n')
            entry = dict(source, dir=str(root), label='malicious', campaign='c',
                         label_provenance=reference(path, source, 'source_malicious'))
            count = lambda text: len(text)
            card = build(entry, count)
            self.assertIsNone(verify(card, count))
            self.assertFalse(card['human_annotation_verified'])
            self.assertEqual(verify(dict(card, code_excerpt='invented'), count), 'excerpt_not_verbatim')
            (root / 'index.js').write_text('changed')
            self.assertEqual(verify(card, count), 'excerpt_hash_mismatch')

    def test_target_archive_selection_uses_exact_package_version_and_rejects_links(self):
        wanted = {('@scope/p', '1.2.3')}
        member = zipfile.ZipInfo('NPMStudy/Dataset/zip_malware/@scope##p/1.2.3/p.tgz')
        self.assertEqual(target_identity(member, wanted), ('@scope/p', '1.2.3'))
        self.assertIsNone(target_identity(member, {('@scope/p', '1.2.4')}))
        member.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            target_identity(member, wanted)

    def test_incremental_campaign_closure_matches_full_clustering(self):
        def item(identity, code, hashes=(), reports=()):
            return dict(id=identity, code=code, code_key=code, reports=reports, added_hashes=hashes)
        old = [item('a', 'A'), item('b', 'B'), item('c', 'C')]
        added = [item('x', 'X', ['h']), item('y', 'Y', ['h']), item('z', 'Z', reports=['r']), item('w', 'W', reports=['r'])]
        related = {frozenset(('A', 'X')), frozenset(('B', 'Y')), frozenset(('C', 'Z'))}
        score = lambda a, b: 0.6 if frozenset((a, b)) in related else 0.0
        actual, edges = extend(old, added, cluster(old, score), score)
        self.assertEqual(actual, cluster(old + added, score))
        self.assertEqual(actual['a'], actual['b'])
        self.assertEqual(actual['c'], actual['w'])


if __name__ == '__main__':
    unittest.main()
