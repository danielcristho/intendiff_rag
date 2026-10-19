"""Usage: python pipeline/source_freeze.py --prep DIR --release DIR."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from capability import declared_dependencies
from expansion_split import exposed_members, merge_review
from samples import load_jsonl
from source_results import verify
from wyss import write_jsonl


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def normalized_cohort(manifest, attempts, exclusions):
    by_id = {r['id']: r for r in attempts}
    if len({r['id'] for r in manifest}) != len(manifest) or {r['id'] for r in manifest} != set(by_id):
        raise ValueError('Normalization coverage differs from candidate manifest')
    failed = {key: row for key, row in by_id.items() if row.get('error')}
    excluded = {r['id']: r for r in exclusions}
    if len(excluded) != len(exclusions) or set(excluded) != set(failed):
        raise ValueError('Every normalization failure needs one explicit technical exclusion')
    for key, record in excluded.items():
        failures = [r for r in attempts if r['id'] == key and r.get('error')]
        if (record.get('reason') != 'normalization_timeout_after_retry'
                or len(failures) < 2 or any(not r['error'].startswith('TimeoutExpired:') for r in failures)
                or record.get('last_error') != failed[key]['error']):
            raise ValueError('Technical exclusion does not match repeated normalization timeout')
    return [r for r in manifest if r['id'] not in excluded], by_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prep', type=Path, required=True)
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    prep, out = args.prep, args.release
    protocol = json.loads((out / 'protocol.json').read_text())
    if protocol.get('test_released'):
        raise ValueError('Test is already frozen; do not overwrite it')
    for name in ('runner', 'configs', 'prompts', 'retrieval_audit', 'source_results', 'output_schema'):
        if digest(Path('pipeline') / (name + '.py')) != digest(out / 'code' / (name + '.py')):
            raise ValueError('Development and test implementations differ: ' + name)
    acquisition_check = json.loads((prep / 'acquisition-verification.json').read_text())
    if acquisition_check.get('verified') is not True:
        raise ValueError('Source acquisition verification has not passed')
    for model in protocol['models']:
        result = verify(out, 'dev', model)
        if not result['complete'] or result['json_validity'] < 0.9:
            raise ValueError('Development format gate has not passed')
    pins = (json.loads((prep / 'normalization-input-pins.json').read_text())
            + json.loads((prep / 'cohort/input-pins.json').read_text())
            + load_jsonl(prep / 'campaigns-with-reports/input-pins.jsonl') + protocol['input_pins']
            + acquisition_check['input_pins'])
    for row in pins:
        if digest(row['path']) != row['sha256']:
            raise ValueError('Preparation input changed: ' + row['path'])
    manifest = load_jsonl(prep / 'cohort/pairs.manifest.jsonl')
    normalized = load_jsonl(prep / 'cohort/pairs.preprocessed.jsonl')
    exclusions_path = prep / 'cohort/technical-exclusions.jsonl'
    exclusions = load_jsonl(exclusions_path)
    candidate_count = len(manifest)
    manifest, by_id = normalized_cohort(manifest, normalized, exclusions)
    if exclusions_path.exists():
        pins.append(dict(path=str(exclusions_path), sha256=digest(exclusions_path)))
    campaigns = json.loads((prep / 'campaigns-with-reports/combined.json').read_text())['campaigns']
    roles = json.loads(Path('data/acquisition/campaigns-20261013/combined-d96.json').read_text())['item_roles']
    acquisition = Path('data/acquisition/expansion-full-20261013')
    review = merge_review([acquisition / 'review.typical-combined.jsonl', acquisition / 'review.hn-combined.jsonl'])
    exposed = exposed_members(campaigns, roles, review, load_jsonl(acquisition / 'exposure-registry.jsonl'))
    exposed_campaigns = {campaigns[i] for i in exposed}
    cards = load_jsonl(out / 'kb.jsonl')
    if cards != load_jsonl(prep / 'cohort/kb.jsonl'):
        raise ValueError('Development and test KB differ')
    dev = load_jsonl(out / 'dev.pairs.jsonl')
    blocked_names = {r['name'] for r in cards + dev}
    blocked_campaigns = {r['campaign'] for r in cards + dev} | exposed_campaigns
    rows = []
    for source in manifest:
        pair = by_id[source['id']]
        for field in ('name', 'before', 'after', 'campaign', 'label', 'label_provenance', 'sha256_before', 'sha256_after'):
            if pair.get(field) != source.get(field):
                raise ValueError('Preprocessing metadata differs: ' + source['id'] + ':' + field)
        if pair['name'] in blocked_names or pair['campaign'] in blocked_campaigns or pair['campaign'] != campaigns[pair['id']]:
            raise ValueError('Test overlaps development or KB: ' + pair['id'])
        before, after = [declared_dependencies(Path(source[s + '_dir'])) for s in ('before', 'after')]
        # Evidence is capped at three entries; exclusion must cover every changed dependency.
        names = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
        names.update(pair.get('retrieval_exclude_names', []))
        for side in ('before', 'after'):
            path = Path(source[side + '_dir']) / 'package.json'
            pins.append(dict(path=str(path), sha256=digest(path)))
        rows.append(dict(pair, evaluation_scope='final_holdout', human_annotation_verified=False,
                         label_origin=pair['label_provenance']['basis'], retrieval_exclude_names=sorted(names)))
    write_jsonl(out / 'test.pairs.jsonl', rows)
    budget = out / 'test-budget'
    subprocess.run([sys.executable, 'pipeline/source_budget.py', '--pairs', str(out / 'test.pairs.jsonl'),
                    '--kb', str(out / 'kb.jsonl'), '--out', str(budget)], check=True)
    (out / 'test.prompt-tokens.jsonl').write_bytes((budget / 'prompt-tokens.jsonl').read_bytes())
    for name in ('source_report.py', 'analysis.py'):
        path = out / 'code' / name
        path.write_bytes((Path('pipeline') / name).read_bytes())
        pins.append(dict(path=str(path), sha256=digest(path)))
    for path in [out / 'test.pairs.jsonl', out / 'test.prompt-tokens.jsonl', out / 'protocol.dev.json',
                 prep / 'cohort/summary.json', prep / 'cohort/exclusions.jsonl',
                 prep / 'cohort/normalization-summary.json',
                 prep / 'acquisition-verification.json',
                 Path('pipeline/source_freeze.py'), Path('pipeline/source_budget.py'),
                 Path('pipeline/source_cards.py'), Path('pipeline/source_cohort.py'),
                 Path('pipeline/source_report.py'), Path('pipeline/analysis.py'),
                 Path('pipeline/label_provenance.py'), Path('pipeline/campaign_extend.py')]:
        pins.append(dict(path=str(path), sha256=digest(path)))
    protocol.update(test_released=True, test_pairs=len(rows), test_expected_generations=len(rows) * 12,
                    candidate_pairs=candidate_count, technical_exclusions=exclusions,
                    test_frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                    input_pins=list({r['path']: r for r in pins}.values()))
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps(dict(test_released=True, pairs=len(rows), expected_generations=len(rows) * 12)), flush=True)


if __name__ == '__main__':
    main()
