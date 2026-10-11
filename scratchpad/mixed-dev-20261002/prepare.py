"""Run from the repository root: .venv/bin/python scratchpad/mixed-dev-20261002/prepare.py."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.mixed_dev import blinded_pair, rank, select_malicious_candidates

OUT = ROOT / 'data/evaluation/mixed-dev-20261002'
REVIEW = ROOT / 'data/review/pairs.jsonl'
HN = ROOT / 'data/evaluation/evidence-dev-20261001/pairs.jsonl'


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def write(name, rows):
    (OUT / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if (OUT / 'selection.json').exists():
    raise SystemExit('Selection already frozen; refusing to overwrite')
hn = read(HN)
assert len(hn) == 32 and all(p['subset'] == 'HN' for p in hn)
mal, eligible = select_malicious_candidates(read(REVIEW), hn)
pairs = sorted(hn + mal, key=lambda p: rank('review-order|' + p['id']))
assert len({p['id'] for p in pairs}) == 64
(OUT / 'annotation').mkdir(parents=True, exist_ok=True)
write('pairs.jsonl', pairs)
write('annotation/pairs.jsonl', [blinded_pair(p, f'review-{n:03d}')
                                for n, p in enumerate(pairs, 1)])
write('mapping.jsonl', [{'review_id': f'review-{n:03d}', 'pair_id': p['id'],
                       'candidate_subset': p['subset'], 'campaign': p.get('campaign'),
                       'before_dir': p.get('before_dir'), 'after_dir': p.get('after_dir'),
                       'historical_exposure': 'D81-D84' if p['subset'] == 'MAL' else 'D85'}
                      for n, p in enumerate(pairs, 1)])
write('dev-exclusions.jsonl', [{k: p[k] for k in ('id', 'name', 'campaign', 'diff_sha256',
      'sha256_before', 'sha256_after', 'sha256_before_tree', 'sha256_after_tree') if k in p}
      for p in pairs])
selection = {
    'decision': 'D86', 'scope': 'exploratory_development_annotation_only',
    'candidate_counts': {'MAL': len(mal), 'HN': len(hn)},
    'eligible_mal_candidates': eligible, 'selected_mal_campaigns': len({p['campaign'] for p in mal}),
    'selection': 'SHA256 D86|campaign then D86|id; unique campaign/name/diff/archive; untruncated <=16000 prior tokens',
    'order': 'SHA256 D86|review-order|id; neutral sequential review IDs',
    'hn_selection': 'All 32 D85 candidates, unchanged',
    'human_annotation_verified': False, 'new_generations': 0,
    'limitations': ['All samples previously exposed; not a fresh holdout',
                   'HN campaign/clone mapping unavailable',
                   'Source labels and predictions hidden; package identity and code remain visible',
                   'No replacement based on annotation outcome; skip stays in attrition accounting',
                   'Full prompt context audit required before future inference'],
    'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in (REVIEW, HN)},
    'artifact_sha256': {str(p.relative_to(OUT)): digest(p) for p in OUT.rglob('*.jsonl')},
    'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in (
        Path(__file__), ROOT / 'pipeline/mixed_dev.py', ROOT / 'docs/decisions.md')},
}
(OUT / 'selection.json').write_text(json.dumps(selection, indent=2) + '\n')
print(json.dumps({k: selection[k] for k in ('candidate_counts', 'eligible_mal_candidates', 'selected_mal_campaigns')}))
