"""Usage: python pipeline/source_cohort.py --campaigns FILE --mal FILE --out DIR (offline)."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import capability
from expansion_split import exposed_members, merge_review
from samples import load_jsonl
from source_cards import build, verify
from wyss import write_jsonl


def ranked(rows):
    return sorted(rows, key=lambda r: hashlib.sha256(('D99|' + r['id']).encode()).hexdigest())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaigns', type=Path, required=True)
    parser.add_argument('--mal', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file('data/upstream/tokenizer-qwen25/tokenizer.json')
    count = lambda text: len(tokenizer.encode(text).ids)
    acquisition = Path('data/acquisition/expansion-full-20261013')
    typ_path = acquisition / 'review.typical-combined.jsonl'
    inventory_path = Path('data/acquisition/datadog.inventory-full.jsonl')
    roles_path = Path('data/acquisition/campaigns-20261013/combined-d96.json')
    mal_source_path = Path('data/acquisition/external-mal-20261014/pair-candidates.jsonl')
    roles = json.loads(roles_path.read_text())['item_roles']
    campaigns = json.loads(args.campaigns.read_text())['campaigns']
    review = merge_review([typ_path, acquisition / 'review.hn-combined.jsonl'])
    exposure = load_jsonl(acquisition / 'exposure-registry.jsonl')
    exposed = exposed_members(campaigns, roles, review, exposure)
    exposed_campaigns = {campaigns[i] for i in exposed}
    sources = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (mal_source_path, typ_path, inventory_path)}
    def attach(row, path, label, basis):
        return dict(row, campaign=campaigns[row['id']], label=label,
                    label_provenance=dict(path=str(path), sha256=sources[path], record_id=row['id'], basis=basis))
    mal, exclusions, per_campaign = [], [], Counter()
    for row in ranked(load_jsonl(args.mal)):
        campaign = campaigns[row['id']]
        reason = ('development_exposure' if campaign in exposed_campaigns else
                  'mal_campaign_cap' if per_campaign[campaign] >= 3 else None)
        if reason:
            exclusions.append(dict(id=row['id'], reason=reason, campaign=campaign))
            continue
        per_campaign[campaign] += 1
        mal.append(attach(row, mal_source_path, 'malicious', 'source_malicious'))
    typical = []
    for row in ranked(load_jsonl(typ_path)):
        reason = ('development_exposure' if campaigns[row['id']] in exposed_campaigns else
                  'pending_hn_diagnostic_overlap' if 'HN' in review[row['id']]['subsets'] else None)
        if reason:
            exclusions.append(dict(id=row['id'], reason=reason, campaign=campaigns[row['id']]))
        else:
            typical.append(attach(row, typ_path, 'benign', 'assumed_benign'))
    blocked = {r['campaign'] for r in mal + typical} | exposed_campaigns
    pool = [attach(r, inventory_path, 'malicious', 'source_malicious')
            for r in load_jsonl(inventory_path)
            if r.get('kind') == 'malicious_intent' and not r.get('error') and r['id'] in campaigns
            and campaigns[r['id']] not in blocked]
    cards, rejected, taken, card_campaigns = [], [], set(), Counter()
    source_cache = {}
    queues = {cap: iter(ranked([r for r in pool if cap in r.get('capabilities', [])])) for cap in capability.CAPABILITIES}
    while len(cards) < 50:
        drew = False
        for cap, queue in queues.items():
            if len(cards) == 50:
                break
            for row in queue:
                if row['id'] in taken or card_campaigns[row['campaign']] >= 2:
                    continue
                taken.add(row['id'])
                try:
                    card = build(row, count, source_cache)
                except (ValueError, OSError) as error:
                    rejected.append(dict(id=row['id'], label='malicious', reason=str(error)))
                    continue
                cards.append(card); card_campaigns[row['campaign']] += 1
                print(json.dumps(dict(cards=len(cards), label='malicious')), flush=True)
                drew = True
                break
        if not drew:
            break
    benign_count = 0
    for row in typical:
        if benign_count == 25:
            break
        if card_campaigns[row['campaign']] >= 2:
            continue
        try:
            card = build(row, count, source_cache)
        except (ValueError, OSError) as error:
            rejected.append(dict(id=row['id'], label='benign', reason=str(error)))
            continue
        cards.append(card); card_campaigns[row['campaign']] += 1; benign_count += 1
        print(json.dumps(dict(cards=len(cards), label='benign')), flush=True)
    card_names = {r['name'] for r in cards}
    holdout = []
    for row in mal + typical:
        if row['campaign'] in card_campaigns or row['name'] in card_names:
            exclusions.append(dict(id=row['id'], reason='reserved_kb_name_or_campaign', campaign=row['campaign']))
        else:
            holdout.append(dict(row, evaluation_scope='candidate_holdout', annotation_status='source_labelled'))
    for card in cards:
        problem = verify(card, count, source_cache)
        if problem:
            raise ValueError(f"Card verification failed: {card['id']}: {problem}")
    write_jsonl(args.out / 'kb.jsonl', cards)
    write_jsonl(args.out / 'pairs.manifest.jsonl', ranked(holdout))
    write_jsonl(args.out / 'exclusions.jsonl', exclusions)
    write_jsonl(args.out / 'card-attrition.jsonl', rejected)
    pins = [dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in [args.campaigns, args.mal, mal_source_path, typ_path, inventory_path, roles_path,
                      acquisition / 'review.hn-combined.jsonl', acquisition / 'exposure-registry.jsonl']]
    (args.out / 'input-pins.json').write_text(json.dumps(pins, indent=2) + '\n')
    summary = dict(status='source-labelled preparation; not frozen for inference',
        pairs=len(holdout), subsets=dict(Counter(r['subset'] for r in holdout)),
        typ_strata=dict(Counter(r.get('group') for r in holdout if r['subset'] == 'TYP')),
        mal_campaigns=len({r['campaign'] for r in holdout if r['subset'] == 'MAL'}),
        cards=dict(Counter(r['label'] for r in cards)), card_attrition=len(rejected),
        exclusions=dict(Counter(r['reason'] for r in exclusions)), human_labels_created=0,
        inferences=0, card_budgets_checked=['qwen25'], final_launch_ready=False)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
