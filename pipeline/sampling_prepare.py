"""Usage: python pipeline/sampling_prepare.py --out data/evaluation/sampling-ablation-20261109."""
import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from configs import CONFIGS
from extension_prepare import digest, pin
from runner import load_jsonl
from sampling_grid import MODELS, SEEDS, TEMPERATURES, cells
from source_results import verify

BASE = Path('data/evaluation/source-rag-v3-20261015')
MAL = Path('data/evaluation/source-rag-mal-20261018')
PROTOCOL_DOC = Path('docs/sampling-ablation-20261109.md')
# REQUEST_CODE must stay byte-identical to the frozen T=0 code, or the
# reference cell no longer reproduces the historical request hashes.
REQUEST_CODE = ('runner.py', 'configs.py', 'prompts.py', 'output_schema.py', 'retrieval_audit.py', 'samples.py')
DRIVER_CODE = ('source_experiment.py', 'source_results.py', 'analysis.py', 'mal_eval_metrics.py',
               'sampling_grid.py', 'sampling_batch.py', 'sampling_report.py')


def historical(tag):
    """Both verified T=0 releases that together hold the 1,997 test pairs."""
    base = json.loads((BASE / 'protocol.json').read_text())
    supplement = json.loads((MAL / tag / 'protocol.json').read_text())
    model, = supplement['models']
    for release, spec in ((BASE, next(m for m in base['models'] if m['tag'] == tag)), (MAL / tag, model)):
        # verify() rewrites its report next to the results; a copy keeps the snapshot untouched.
        with tempfile.TemporaryDirectory() as scratch:
            for name in ('test.pairs.jsonl', 'kb.jsonl', 'test.prompt-tokens.jsonl', f'test.{tag}.results.jsonl'):
                shutil.copyfile(release / name, Path(scratch) / name)
            if not verify(scratch, 'test', spec)['complete']:
                raise ValueError(f'Historical T=0 results are not verified complete: {release}')
    return model, [BASE / f'test.{tag}.results.jsonl', MAL / tag / f'test.{tag}.results.jsonl']


def combined_pairs(tags):
    pairs = load_jsonl(BASE / 'test.pairs.jsonl') + load_jsonl(MAL / tags[0] / 'test.pairs.jsonl')
    if any(load_jsonl(MAL / tag / 'test.pairs.jsonl') != pairs[1901:] for tag in tags):
        raise ValueError('MAL supplement differs between models')
    mal = [p for p in pairs if p['label'] == 'malicious']
    if len({p['id'] for p in pairs}) != 1997 or len(mal) != 129 or len({p['campaign'] for p in mal}) != 98:
        raise ValueError('Expected 1,997 unique pairs with 129 MAL in 98 campaigns')
    if sum(p['label'] == 'benign' for p in pairs) != 1868:
        raise ValueError('Expected 1,868 TYP')
    return pairs


def prompt_tokens(models, pairs):
    ids = {m['id'] for m in models}
    rows = [r for r in load_jsonl(BASE / 'test.prompt-tokens.jsonl') if r['model'] in ids]
    for model in models:
        rows += load_jsonl(MAL / model['tag'] / 'test.prompt-tokens.jsonl')
    expected = {(m['id'], p['id'], c) for m in models for p in pairs for c in CONFIGS}
    if len(rows) != len(expected) or {(r['model'], r['pair_id'], r['config']) for r in rows} != expected:
        raise ValueError('Audited prompt tokens do not cover the combined test set exactly')
    return rows


def write_jsonl(path, rows):
    # Escaped on purpose: load_jsonl uses str.splitlines, which also breaks on
    # U+2028 and similar characters that some diffs contain.
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))


def prepare(out):
    if not PROTOCOL_DOC.exists():
        raise ValueError(f'Write the protocol before freezing: {PROTOCOL_DOC}')
    if (BASE / 'kb.jsonl').read_bytes() != (MAL / MODELS[0] / 'kb.jsonl').read_bytes():
        raise ValueError('Knowledge base differs between historical releases')
    specs = {tag: historical(tag) for tag in MODELS}
    models = [specs[tag][0] for tag in MODELS]
    pairs = combined_pairs(MODELS)
    tokens = prompt_tokens(models, pairs)
    for name in REQUEST_CODE:
        if digest(Path('pipeline') / name) != digest(BASE / 'code' / name):
            raise ValueError(f'Request code changed since the T=0 run: {name}')
    out.mkdir(parents=True)
    code = out / 'code'
    code.mkdir()
    for name in REQUEST_CODE + DRIVER_CODE:
        shutil.copyfile(Path('pipeline') / name, code / name)
    shutil.copyfile(BASE / 'kb.jsonl', out / 'kb.jsonl')
    shutil.copyfile(BASE / 'dev.pairs.jsonl', out / 'dev.pairs.jsonl')
    write_jsonl(out / 'test.pairs.jsonl', pairs)
    write_jsonl(out / 'test.prompt-tokens.jsonl', tokens)
    base = json.loads((BASE / 'protocol.json').read_text())
    runtime = json.loads((BASE / 'runtime-observation.json').read_text())
    pins = [pin(p) for p in sorted(out.rglob('*')) if p.is_file()]
    pins += [pin(BASE / 'protocol.json'), pin(PROTOCOL_DOC)]
    pins += [pin(path) for tag in MODELS for path in specs[tag][1]]
    per_cell = len(pairs) * len(CONFIGS)
    protocol = dict(decision='D111', role='sampling ablation; the main results stay T=0 seed 0 and no decoding '
                    'setting is selected from this grid', frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                    configs=list(CONFIGS), max_tokens=base['max_tokens'], response_format=base['response_format'],
                    temperatures=list(TEMPERATURES), seeds=list(SEEDS), top_p=1.0, top_k=None,
                    warmup_per_model_session=base['warmup_per_model_session'], models=models,
                    runtime=dict(python=runtime['python'], packages=runtime['packages']),
                    test_pairs=len(pairs), mal_pairs=129, mal_campaigns=98, typ_pairs=1868,
                    cell_expected_generations=per_cell,
                    total_expected_generations=per_cell * len(cells()) * len(models),
                    historical={tag: [str(p) for p in specs[tag][1]] for tag in MODELS},
                    dev_gate='not rerun: the T=0 format gate already passed; validity is reported per cell',
                    invalid_policy='benign primary; malicious sensitivity',
                    label_policy=base['label_policy'], input_pins=pins)
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    return protocol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    protocol = prepare(parser.parse_args().out)
    print(json.dumps({k: v for k, v in protocol.items() if k not in ('input_pins', 'models', 'response_format')},
                     indent=2))


if __name__ == '__main__':
    main()
