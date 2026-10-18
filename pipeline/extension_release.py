"""Usage: python pipeline/extension_release.py --release DIR."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    out = args.release
    sys.path.insert(0, str(out / 'code'))
    from source_experiment import check_pins, digest
    from source_results import verify
    protocol = json.loads((out / 'protocol.json').read_text())
    model, = protocol['models']
    check_pins(protocol, model)
    dev = verify(out, 'dev', model)
    if not dev['complete'] or dev['json_validity'] < 0.9:
        raise ValueError('Development JSON gate failed; no test inference permitted')
    budget = json.loads((out / 'budget.json').read_text())
    if not budget['ready'] or any(s['max_prompt_tokens'] + 512 > model['max_model_len'] for s in budget['stages'].values()):
        raise ValueError('Model context gate failed')
    parent = Path(protocol['parent_release'])
    for name in ('dev.pairs.jsonl', 'test.pairs.jsonl', 'kb.jsonl'):
        if digest(parent / name) != digest(out / name):
            raise ValueError('Additional model input differs from primary experiment')
    if not protocol['test_released']:
        protocol.update(test_released=True, model_test_released_at_utc=datetime.now(timezone.utc).isoformat())
        for path in [out / 'protocol.dev.json', Path(__file__)]:
            protocol['input_pins'].append(dict(path=str(path), sha256=digest(path)))
        temporary = out / 'protocol.tmp.json'
        temporary.write_text(json.dumps(protocol, indent=2) + '\n')
        temporary.replace(out / 'protocol.json')
    print(json.dumps(dict(model=model['tag'], test_released=True, dev_json_validity=dev['json_validity'])), flush=True)


if __name__ == '__main__':
    main()
