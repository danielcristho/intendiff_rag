"""Report comparable complete model cohorts and retain invalid-answer sensitivity."""
import json
import statistics

from common import ARMS, HERE, read_rows, validate_rows, write_json


def summarize(model, pairs, rows):
    assert len(validate_rows(rows, model, pairs)) == len(pairs) * len(ARMS)
    groups = []
    for arm in ARMS:
        selected = [r for r in rows if r['arm'] == arm]
        mal = [r for r in selected if r['label'] == 'malicious']
        typ = [r for r in selected if r['label'] == 'benign']
        assert len(mal) == 873 and len(typ) == 100
        positive = lambda r: r['json_valid'] and r['parsed']['verdict'] == 'malicious'
        invalid = lambda r: not r['json_valid']
        groups.append({'model': model['id'], 'arm': arm, 'responses': len(selected),
            'mal_detected': sum(map(positive, mal)), 'mal_total': len(mal),
            'recall_source': sum(map(positive, mal)) / len(mal),
            'typ_false_alarms': sum(map(positive, typ)), 'typ_total': len(typ),
            'fpr_assumed_benign_typ': sum(map(positive, typ)) / len(typ),
            'json_valid': sum(r['json_valid'] for r in selected),
            'length_limited': sum(r['finish_reason'] == 'length' for r in selected),
            'unknown_id_responses': sum(bool(r.get('citation_audit', {}).get('unknown_ids')) for r in selected),
            'recall_invalid_as_malicious': sum(positive(r) or invalid(r) for r in mal) / len(mal),
            'fpr_invalid_as_malicious': sum(positive(r) or invalid(r) for r in typ) / len(typ),
            'total_tokens': sum(r['usage']['prompt_tokens'] + r['usage']['completion_tokens'] for r in selected),
            'median_latency_ms': statistics.median(r['latency_ms'] for r in selected),
            'human_annotation_verified': False})
    return groups


def report():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    pairs = read_rows(HERE / 'pairs.jsonl')
    groups, missing = [], []
    for model in protocol['models']:
        verified = HERE / f"{model['tag']}.verification.json"
        if not verified.exists():
            missing.append(model['id'])
            continue
        assert json.loads(verified.read_text())['verified']
        groups += summarize(model, pairs, read_rows(HERE / f"{model['tag']}.results.jsonl"))
    result = {'complete': not missing, 'missing_models': missing, 'groups': groups,
              'scope': 'full source-labelled cohort; updated ID/schema/verifier method',
              'historical_responses_included': 0, 'expected_new_generations': 20433}
    write_json(HERE / 'summary.json', result)
    lines = ['# Perbandingan model — implementasi diff ber-ID, schema dan verifier', '',
             'Status: ' + ('lengkap' if not missing else 'belum lengkap; model belum selesai: ' + ', '.join(missing)), '',
             'Setiap baris lengkap mencakup 873 MAL label sumber + 100 TYP diasumsikan benign. Invalid dihitung benign; sensitivitas ada di JSON.', '',
             '| Model | Metode | Deteksi sumber | Alarm salah TYP | JSON valid |',
             '|---|---|---:|---:|---:|']
    names = {'IDS-D': 'DIFF (ID)', 'IDS-I': 'DIFF+I (ID)', 'VERIFY-I': 'DIFF+I+verifier (ID)'}
    for g in groups:
        lines.append(f"| {g['model']} | {names[g['arm']]} | {100*g['recall_source']:.2f}% | "
                     f"{100*g['fpr_assumed_benign_typ']:.2f}% | {g['json_valid']}/973 |")
    lines += ['', 'Verifier uses an additional IDS-I request per target. Its total cost is IDS-I plus VERIFY-I; labels are not human gold.']
    (HERE / 'comparison.md').write_text('\n'.join(lines) + '\n')
    return result


if __name__ == '__main__':
    report()
