"""Post-hoc descriptive strata based on observed dependency changes; no relabeling."""
import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/mixed-validation-20261011'
sys.path.insert(0, str(HERE))
from evidence import index_diff

read = lambda name: [json.loads(line) for line in (HERE / name).open()]
pairs, rows = read('pairs.jsonl'), read('results.jsonl')
features = []
for pair in pairs:
    added = [r['text'] for r in index_diff(pair['diff']) if r['kind'] == 'added']
    changed_paths = sorted({r['path'] for r in index_diff(pair['diff'])
                            if r['path'] and r['kind'] in ('added', 'deleted')})
    features.append({'pair_id': pair['id'], 'campaign': pair['campaign'], 'changed_paths': changed_paths,
                     'adds_easy_day_js': any('"easy-day-js"' in line for line in added),
                     'package_json_only': changed_paths == ['package.json']})
strata = []
for feature in ('adds_easy_day_js', 'package_json_only'):
    for value in (True, False):
        ids = {p['pair_id'] for p in features if p[feature] == value}
        for arm in ('LEGACY-I', 'SCHEMA-I', 'IDS-I', 'IDS-D', 'VERIFY-I'):
            selected = [r for r in rows if r['pair_id'] in ids and r['arm'] == arm]
            strata.append({'feature': feature, 'value': value, 'arm': arm, 'n': len(selected),
                           'positive': sum(r['json_valid'] and r['parsed']['verdict'] == 'malicious' for r in selected),
                           'invalid': sum(not r['json_valid'] for r in selected)})
changes = [r for r in read('changed-verdicts.jsonl') if r['cohort'] == 'MAL'
           and r['before'] == 'SCHEMA-I' and r['before_state'] == 'malicious' and r['after_state'] == 'benign']
feature_map = {r['pair_id']: r for r in features}
result = {'scope': 'post_hoc_descriptive_not_confirmatory', 'features': features, 'strata': strata,
          'lost_schema_positives': len(changes),
          'lost_schema_positives_adding_easy_day_js': sum(feature_map[r['pair_id']]['adds_easy_day_js'] for r in changes),
          'limitation': 'Shared dependency indicators do not prove common campaign, but distinct current cluster IDs do not prove incident independence.'}
(HERE / 'representation-strata.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'features'}, indent=2))
