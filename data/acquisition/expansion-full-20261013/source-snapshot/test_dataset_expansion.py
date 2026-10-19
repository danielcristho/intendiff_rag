import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
import capability
from expansion_fetch import package_queue, pairs_at_cutoff
from expansion_inventory import screen_typical
from expansion_screen import compare_versions, inspect_archive, select_candidates
from expansion_report import hn_reasons


class ExpansionTests(unittest.TestCase):
    def test_hn_requires_both_advisory_checks_and_an_unchanged_known_publisher(self):
        row = dict(same_publisher=True, earlier_unavailable_pairs=[])
        clean = dict(has_advisory=False)
        self.assertEqual(hn_reasons(row, [clean, clean]), [])
        self.assertIn('advisory_check_missing', hn_reasons(row, [clean, None]))
        self.assertIn('advisory_present', hn_reasons(row, [dict(has_advisory=True), clean]))
        self.assertIn('publisher_changed_or_missing', hn_reasons(dict(row, same_publisher=False), [clean, clean]))

    def test_missing_advisory_is_not_benign_and_hn_overlap_is_retained(self):
        rows = [dict(id='pkg@2', name='pkg', before='1', after='2', group='random')]
        extracted = {('pkg', v): dict(dir=v, sha256=v) for v in ('1', '2')}
        checks = {('pkg', v): dict(has_advisory=False) for v in ('1', '2')}
        accepted, rejected = screen_typical(rows, extracted, checks, [], {'pkg@2'})
        self.assertEqual(len(accepted), 1)
        self.assertTrue(accepted[0]['overlaps_hn'])
        self.assertIsNone(accepted[0]['gold_label'])
        self.assertFalse(accepted[0]['holdout_eligible'])
        del checks[('pkg', '2')]
        accepted, rejected = screen_typical(rows, extracted, checks, [], set())
        self.assertFalse(accepted)
        self.assertIn('advisory_check_missing', rejected[0]['reasons'])

    def test_related_dependency_is_quarantined_without_hiding_candidate(self):
        rows = [dict(id='pkg@2', name='pkg', before='1', after='2')]
        versions = {('pkg', v): dict(dir=v, sha256=v) for v in ('1', '2')}
        checks = {('pkg', v): dict(has_advisory=False) for v in ('1', '2')}
        exposures = [dict(id='other@1', name='other', related_names=['pkg'])]
        accepted, _ = screen_typical(rows, versions, checks, exposures, set())
        self.assertTrue(accepted[0]['related_dependency_exposed'])
        self.assertFalse(accepted[0]['pair_exposed'])

    def test_search_rank_is_applied_before_any_screening(self):
        rows = [dict(name=f'p{i}', search_category=1, inspection_rank=i,
                     keywords=['postinstall'], metadata_files=[]) for i in (1, 250, 251)]
        queue = package_queue(rows)
        self.assertEqual({r['name'] for r in queue}, {'p1', 'p250'})
        self.assertEqual(queue, package_queue(list(reversed(rows))))

    def test_future_and_undated_versions_cannot_enter_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'metadata.json'
            versions = ['1.0.0', '1.1.0', '1.2.0', '2.0.0']
            document = dict(name='pkg', versions={v: dict(name='pkg', version=v) for v in versions},
                            time={'1.0.0': '2025-01-01T00:00:00Z',
                                  '1.1.0': '2025-02-01T00:00:00Z',
                                  '2.0.0': '2027-01-01T00:00:00Z'})
            path.write_text(json.dumps(document))
            row = dict(name='pkg', metadata_file=str(path), metadata_sha256='pin', searches=[])
            pairs, missing = pairs_at_cutoff(row, datetime(2026, 1, 1, tzinfo=timezone.utc))
            self.assertEqual([(r['before'], r['after']) for r in pairs], [('1.0.0', '1.1.0')])
            self.assertEqual(missing, ['1.2.0'])

    def test_static_cache_matches_existing_delta_and_rejects_escaping_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = []
            for version, files in [('1.0.0', {'old.txt': 'old'}), ('1.1.0', {
                'index.js': "require('https'); require('child_process');",
                'README.md': 'Documented package purpose'})]:
                manifest = dict(name='pkg', version=version)
                if version == '1.1.0':
                    manifest.update(scripts={'postinstall': 'node index.js'}, dependencies={'dep': '^1'})
                files['package.json'] = json.dumps(manifest)
                archive = root / f'{version}.tgz'
                with tarfile.open(archive, 'w:gz') as tar:
                    for name, text in files.items():
                        member = tarfile.TarInfo('package/' + name)
                        payload = text.encode()
                        member.size = len(payload)
                        tar.addfile(member, io.BytesIO(payload))
                row = dict(name='pkg', version=version, tarball=str(archive),
                           sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
                result = inspect_archive(row, root / 'work')
                self.assertNotIn('error', result)
                results.append(result)
            delta, evidence = compare_versions(*results)
            self.assertEqual(delta, capability.delta(results[0]['dir'], results[1]['dir']))
            self.assertEqual(evidence, capability.delta_evidence(results[0]['dir'], results[1]['dir']))
            with tarfile.open(archive, 'w:gz') as tar:
                member = tarfile.TarInfo('../escape')
                member.size = 1
                tar.addfile(member, io.BytesIO(b'x'))
            row['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertIn('error', inspect_archive(row, root / 'work'))
            self.assertFalse((root / 'escape').exists())

    def test_unavailable_earlier_pair_never_becomes_clean_earliest_selection(self):
        pairs = [dict(id=f'p@{v}', name='p', before=str(v-1), after=str(v),
                      pair_order=v, searches=[{'search_category': 2}]) for v in (1, 2)]
        scan = dict(dir='dir', sha256='sha', tree_sha256='tree', purpose_documents=[],
                    capabilities=[], hooks={}, dependencies={}, text_files=['package.json'], evidence={})
        scans = {('p', '1'): scan, ('p', '2'): dict(scan, capabilities=['network'], evidence={'network': []})}
        _, selected = select_candidates(pairs, scans)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['earlier_unavailable_pairs'], ['p@1'])
        self.assertIsNone(selected[0]['gold_label'])


if __name__ == '__main__':
    unittest.main()
