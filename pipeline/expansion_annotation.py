"""Usage: python pipeline/expansion_annotation.py --review FILE --split FILE --out DIR."""
import argparse
import hashlib
import json
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl

REVIEW_FIELDS = ('id', 'name', 'before', 'after', 'before_dir', 'after_dir',
                 'delta', 'delta_evidence', 'purpose_documents_before', 'purpose_documents_after')


def prepare(review, splits):
    by_id = {r['id']: r for r in review}
    if len(by_id) != len(review) or len({r['id'] for r in splits}) != len(splits):
        raise ValueError('Duplicate review or split IDs')
    selected = [r for r in splits if r['proposed_partition'] == 'hn-pending-annotation']
    rows, forms = [], []
    for split in sorted(selected, key=lambda r: hashlib.sha256(('annotation-20261013|' + r['id']).encode()).hexdigest()):
        if not split['holdout_eligible'] or split['final'] or split['gold_label'] is not None:
            raise ValueError('Expected provisional, eligible, unlabelled candidates')
        row = by_id[split['id']]
        rows.append({key: row[key] for key in REVIEW_FIELDS if key in row})
        forms.append(dict(id=row['id'], label=None, category=None, purpose_evidence=[],
                          malicious_evidence=[], notes='', status='pending'))
    return rows, forms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', required=True)
    parser.add_argument('--split', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    rows, forms = prepare(load_jsonl(args.review), load_jsonl(args.split))
    write_jsonl(out / 'materials.jsonl', rows)
    for annotator in ('A', 'B'):
        write_jsonl(out / f'annotation.{annotator}.jsonl', [dict(r, annotator=annotator) for r in forms])
    pins = []
    for name in (args.review, args.split, __file__):
        path = Path(name)
        pins.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    summary = dict(status='source review only; final normalized smartdiff evidence pending',
                   candidates=len(rows), gold_labels_created=0, inferences=0,
                   distinct_human_annotators_required=2, input_pins=pins)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
