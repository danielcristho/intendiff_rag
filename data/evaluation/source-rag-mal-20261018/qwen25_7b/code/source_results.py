"""Verify source-labelled experiment coverage and summarize observed predictions."""
import json
from collections import Counter
from pathlib import Path

from configs import CONFIGS
from runner import build, parse_verdict, request_hash, retrieve, retrieval_log, run_key
from samples import load_jsonl
from output_schema import SCHEMA
import jsonschema


def verify(directory, stage, model):
    directory = Path(directory)
    pairs = {r['id']: r for r in load_jsonl(directory / f'{stage}.pairs.jsonl')}
    cards = load_jsonl(directory / 'kb.jsonl')
    rows = load_jsonl(directory / f'{stage}.{model["tag"]}.results.jsonl')
    tokens = {(r['pair_id'], r['config']): r['prompt_tokens']
              for r in load_jsonl(directory / f'{stage}.prompt-tokens.jsonl') if r['model'] == model['id']}
    expected = {(p, c) for p in pairs for c in CONFIGS}
    unique = {}
    for row in rows:
        key = (row['pair_id'], row['config'])
        if key not in expected or row['model'] != model['id']:
            raise ValueError('Unexpected model, pair or configuration')
        if row['run_key'] != run_key(model['id'], key[1], key[0], 0, 0.0):
            raise ValueError('Unexpected run key')
        if (row.get('seed'), row.get('temperature'), row.get('top_p'), row.get('top_k')) != (0, 0.0, 1.0, None):
            raise ValueError('Unexpected sampling parameters')
        if row.get('error'):
            continue
        if key in unique:
            raise ValueError('Duplicate completed generation')
        pair = pairs[key[0]]
        payload_hash = request_hash(model['id'], build(key[1], pair, retrieve(key[1], pair, cards)), 0,
                                    dict(temperature=0.0, top_p=1.0))
        if row.get('request_sha256') != payload_hash or row.get('response_model') != model['id'] or not row.get('response_id'):
            raise ValueError('Request or response identity differs')
        if row['label'] != pair['label'] or row['diff_sha256'] != pair['diff_sha256']:
            raise ValueError('Result source label or diff differs')
        if row['cards'] != retrieval_log(pair, retrieve(key[1], pair, cards)):
            raise ValueError('Result retrieval differs')
        if row['prompt_tokens'] != tokens[key] or not 0 < row['completion_tokens'] <= 512:
            raise ValueError('Result token counts differ from audited request')
        parsed = parse_verdict(row['raw'])
        if row['json_valid'] != (parsed is not None and row['finish_reason'] != 'length'):
            raise ValueError('Result JSON validity cannot be reproduced')
        for field in ('verdict', 'evidence', 'reason'):
            if row[field] != (parsed or {}).get(field):
                raise ValueError('Parsed result differs from saved response')
        if row['json_valid']:
            raw_object, _ = json.JSONDecoder().raw_decode(row['raw'][row['raw'].index('{'):])
            jsonschema.validate(raw_object, SCHEMA)
        unique[key] = row
    if len({r['response_id'] for r in unique.values()}) != len(unique):
        raise ValueError('Duplicate response IDs')
    groups = []
    for config in CONFIGS:
        selected = [r for (p, c), r in unique.items() if c == config]
        for invalid_as in ('benign', 'malicious'):
            confusion, strata = Counter(), {}
            for row in selected:
                pair = pairs[row['pair_id']]
                prediction = row['verdict'] if row['json_valid'] else invalid_as
                positive = prediction == 'malicious'
                truth = pair['label'] == 'malicious'
                confusion[('TP' if positive else 'FN') if truth else ('FP' if positive else 'TN')] += 1
                if pair['subset'] == 'TYP':
                    group = strata.setdefault(pair.get('group', 'unspecified'), dict(n=0, alarms=0))
                    group['n'] += 1; group['alarms'] += positive
            tp, fn, tn, fp = (confusion[x] for x in ('TP', 'FN', 'TN', 'FP'))
            tpr = tp / (tp + fn) if tp + fn else None
            specificity = tn / (tn + fp) if tn + fp else None
            groups.append(dict(config=config, invalid_as=invalid_as, completed=len(selected),
                expected=len(pairs), confusion=dict(confusion), tpr_source=tpr,
                cohort_accuracy=(tp + tn) / len(selected) if selected else None,
                balanced_accuracy=(tpr + specificity) / 2 if tpr is not None and specificity is not None else None,
                typ_strata=strata, invalid=sum(not r['json_valid'] for r in selected)))
    result = dict(model=model['id'], stage=stage, complete=set(unique) == expected,
                  completed=len(unique), expected=len(expected),
                  transport_attempt_errors=sum(bool(r.get('error')) for r in rows),
                  json_validity=sum(r['json_valid'] for r in unique.values()) / len(unique) if unique else None,
                  label_policy='source MAL; assumed-benign TYP; no human gold', groups=groups)
    (directory / f'{stage}.{model["tag"]}.verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
