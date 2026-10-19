"""Usage: python pipeline/mal_eval_prepare.py --out DIR [--tag TAG --parent DIR]."""
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from extension_prepare import digest, pin, replace_once

ACQUISITION = Path('data/acquisition/mal-expansion-20261017')
BASE = Path('data/evaluation/source-rag-v3-20261015')
EXTRA = Path('data/evaluation/source-rag-extra-20261016')
HELPERS = ('mal_eval_prepare.py', 'mal_eval_batch.py', 'mal_eval_report.py', 'mal_eval_metrics.py')


def check_candidates(pairs):
    if len(pairs) != 96 or len({p['id'] for p in pairs}) != 96:
        raise ValueError('Expected exactly 96 unique frozen candidates')
    if len({p['campaign'] for p in pairs}) != 65:
        raise ValueError('Expected 65 candidate campaigns')
    if any(p['label'] != 'malicious' or p['subset'] != 'MAL' for p in pairs):
        raise ValueError('Supplement must contain source MAL only')


def prepare(out, parent, tag):
    baseline = json.loads((parent / 'protocol.json').read_text())
    model = next(m for m in baseline['models'] if m['tag'] == tag)
    sys.path.insert(0, str((parent / 'code').resolve()))
    from source_experiment import check_pins
    from source_results import verify
    from samples import load_jsonl
    check_pins(baseline, model)
    dev = verify(parent, 'dev', model)
    if not dev['complete'] or dev['json_validity'] < 0.9:
        return dict(tag=tag, eligible=False, reason='historical_dev_format_gate_failed',
                    dev_json_validity=dev['json_validity'])
    if not baseline['test_released'] or not verify(parent, 'test', model)['complete']:
        raise ValueError('Historical evaluation is not verified complete')
    preparation = json.loads((ACQUISITION / 'preparation-verification.json').read_text())
    if not preparation['verified'] or not preparation['source_trees_unchanged']:
        raise ValueError('Acquisition verification failed')
    for row in preparation['input_pins']:
        if digest(row['path']) != row['sha256']:
            raise ValueError('Acquisition input changed: ' + row['path'])
    pairs = load_jsonl(ACQUISITION / 'pairs.prepared.jsonl')
    check_candidates(pairs)
    old_ids = {p['id'] for p in load_jsonl(parent / 'test.pairs.jsonl')}
    if old_ids & {p['id'] for p in pairs}:
        raise ValueError('Supplement overlaps historical test identities')
    out.mkdir()
    code = out / 'code'
    shutil.copytree(parent / 'code', code, ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('dev.pairs.jsonl', 'kb.jsonl', f'dev.{tag}.results.jsonl', 'model-options.json'):
        if (parent / name).exists():
            shutil.copyfile(parent / name, out / name)
    shutil.copyfile(ACQUISITION / 'pairs.prepared.jsonl', out / 'test.pairs.jsonl')
    (out / 'model.json').write_text(json.dumps(model, indent=2) + '\n')
    with (out / 'budget.log').open('w') as log:
        subprocess.run([sys.executable, '-u', 'pipeline/extension_audit.py', '--release', str(out)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    budget = json.loads((out / 'budget.json').read_text())
    driver = (code / 'source_experiment.py').read_text()
    for option, literal, field in (('--max-model-len', '32768', 'max_model_len'),
                                  ('--kv-cache-memory-bytes', '6442450944', 'kv_cache_memory_bytes')):
        if f"'{option}', '{literal}'" in driver:
            driver = replace_once(driver, f"'{option}', '{literal}'", f"'{option}', str(model['{field}'])")
    (code / 'source_experiment.py').write_text(driver)
    model = dict(model, **{k: budget[k] for k in ('max_model_len', 'kv_cache_memory_bytes')})
    # Reuse dev predictions only when the exact request hashes still verify.
    reused = verify(out, 'dev', model)
    if not reused['complete'] or reused['json_validity'] < 0.9:
        raise ValueError('Reused development responses failed verification')
    pins = baseline['input_pins'] + preparation['input_pins']
    pins += [pin(parent / 'protocol.json'), pin(parent / f'test.{tag}.results.jsonl'),
             pin(parent / f'dev.{tag}.results.jsonl'), pin(ACQUISITION / 'preparation-verification.json')]
    pins += [pin(Path('pipeline') / name) for name in (*HELPERS, 'extension_audit.py', 'extension_prepare.py')]
    pins += [pin('docs/mal-evaluation-20261018.md')]
    pins += [pin(p) for p in sorted(out.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.log']
    protocol = {k: baseline[k] for k in ('configs', 'max_tokens', 'temperature', 'seed',
                'warmup_per_model_session', 'dev_validity_threshold', 'response_format')}
    protocol.update(decision='D105', parent_release=str(parent), models=[model],
                    frozen_at_utc=datetime.now(timezone.utc).isoformat(), test_released=True,
                    input_pins=list({r['path']: r for r in pins}.values()),
                    dev_pairs=10, dev_expected_generations=60, test_pairs=96,
                    test_expected_generations=576, campaign_count=65,
                    max_model_len=model['max_model_len'], kv_cache_memory_bytes=model['kv_cache_memory_bytes'],
                    label_policy='source MAL; no human gold; predecessor screening is not proof of benignity',
                    human_gold=False, dev_reused_from=str(parent),
                    evaluation_role='MAL-only supplement selected after historical test results; descriptive',
                    invalid_policy='benign primary; malicious sensitivity',
                    report_policy='new TPR separate; old FPR and combined cohort metrics descriptive only')
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    return dict(tag=tag, eligible=True, expected=576, dev_json_validity=reused['json_validity'],
                max_prompt_tokens=budget['stages']['test']['max_prompt_tokens'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--tag')
    parser.add_argument('--parent', type=Path)
    args = parser.parse_args()
    if args.tag:
        result = prepare(args.out / args.tag, args.parent, args.tag)
        (args.out / f'{args.tag}.preparation.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        return
    args.out.mkdir(parents=True, exist_ok=False)
    sources = [(BASE, m['tag']) for m in json.loads((BASE / 'protocol.json').read_text())['models']]
    sources += [(EXTRA / tag, tag) for tag in json.loads((EXTRA / 'manifest.json').read_text())['models']]
    manifest = dict(decision='D105', models=[], excluded=[], errors=[], planned=[tag for _, tag in sources])
    for parent, tag in sources:
        result = subprocess.run([sys.executable, '-u', __file__, '--out', str(args.out),
                                 '--tag', tag, '--parent', str(parent)])
        if result.returncode:
            manifest['errors'].append(dict(tag=tag, returncode=result.returncode))
        else:
            row = json.loads((args.out / f'{tag}.preparation.json').read_text())
            if row['eligible']:
                manifest['models'].append(tag)
            else:
                manifest['excluded'].append(row)
        (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    if manifest['errors']:
        raise SystemExit('Preparation errors: no batch launch until reviewed')


if __name__ == '__main__':
    main()
