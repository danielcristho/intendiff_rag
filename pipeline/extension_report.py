"""Usage: python pipeline/extension_report.py --out DIR."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.out
    manifest = json.loads((root / 'manifest.json').read_text())
    releases = [Path(manifest['parent_release'])] + [root / tag for tag in manifest['models']]
    metrics, coverage, sources = [], [], []
    text = ['# Perbandingan RAG D101 dan tambahan D102', '',
            'Dua model utama selesai sebelum pemilihan lima model tambahan. Semua memakai '
            '1.901 pair dan 75 card identik. MAL label sumber (33), TYP assumed-benign (1.868); '
            'akurasi cohort bukan estimasi populasi. Invalid dihitung benign pada tabel utama. '
            'Perbedaan tokenizer, chat template, konteks dan cache tercatat per model.', '',
            '| Model | Konfigurasi | TPR MAL | FPR TYP | Akurasi cohort | Balanced accuracy | Invalid |',
            '|---|---|---|---|---|---|---|']
    for release in releases:
        summary = release / 'summary.json'
        if not summary.exists():
            coverage.append(dict(release=str(release), complete=False))
            continue
        protocol = json.loads((release / 'protocol.json').read_text())
        if not protocol['test_released']:
            raise ValueError('Summary exists for unreleased test')
        for model in protocol['models']:
            checked = json.loads((release / f'test.{model["tag"]}.verification.json').read_text())
            if not checked['complete'] or checked['completed'] != 11406:
                raise ValueError('Summary does not have a complete verified matrix')
            coverage.append(dict(model=model['id'], release=str(release), complete=True))
        sources.append(dict(path=str(summary), sha256=hashlib.sha256(summary.read_bytes()).hexdigest()))
        tags = {model['id']: model['tag'] for model in protocol['models']}
        for row in json.loads(summary.read_text())['metrics']:
            metrics.append(row)
            if row['invalid_as'] != 'benign':
                continue
            confusion = row['confusion']
            fp, tn = confusion.get('FP', 0), confusion.get('TN', 0)
            if fp + tn != 1868 or confusion.get('TP', 0) + confusion.get('FN', 0) != 33:
                raise ValueError('Reported cohort composition differs')
            text.append(f"| {tags[row['model']]} | {row['config']} | {row['tpr_source']:.2%} | "
                        f"{fp / (fp + tn):.2%} | {row['cohort_accuracy']:.2%} | "
                        f"{row['balanced_accuracy']:.2%} | {row['invalid']} |")
    completed = sum(row['complete'] for row in coverage)
    text[2:2] = [f'**Cakupan: {completed}/7 model selesai.** Model yang belum selesai tidak diisi dengan angka perkiraan.', '']
    text += ['', 'CI Wilson, FPR per strata, sensitivitas invalid dan perbandingan paired tersedia '
             'di results.md/summary.json tiap model. Tabel ini menggabungkan ringkasan yang sudah '
             'lolos verifier; tidak menggabungkan hasil D92 tanpa RAG.', '']
    (root / 'comparison.md').write_text('\n'.join(text))
    (root / 'comparison.json').write_text(json.dumps(dict(complete=completed == 7, coverage=coverage,
                                                        metrics=metrics, sources=sources), indent=2) + '\n')
    print(str(root / 'comparison.md'), flush=True)


if __name__ == '__main__':
    main()
