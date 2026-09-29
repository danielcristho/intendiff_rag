"""Export the exploratory metrics as a readable report and a CSV table."""
import csv


def write_report(summary, directory):
    groups = summary["groups"]
    def cell(value):
        return f"{value['positive']}/{value['n']} ({100*value['rate']:.2f}%)" if value['n'] else 'belum tersedia'

    lines = ['# Evaluasi baseline data asli — 29 September 2026', '',
             '**Eksploratif terhadap label sumber; bukan evaluasi gold atau hasil konfirmatori.**', '',
             f"Diperbarui: {summary['generated_at_utc']}.", '',
             f"Run selesai: {sum(g['completed'] for g in groups)}/{summary['expected_runs']}. "
             f"Status lengkap: {summary['complete']}.", '',
             'Dataset: 873 MAL berlabel sumber + 100 TYP yang diasumsikan benign. '
             'Seluruh pair dipakai pada DIFF dan DIFF+I untuk kedua model, greedy/seed 0.', '',
             '| Model | Konfigurasi | MAL ditandai malicious | FPR TYP | JSON valid | Median ms | p95 ms |',
             '|---|---|---:|---:|---:|---:|---:|']
    for group in groups:
        valid_cell = f"{group['json_valid']}/{group['completed']}" if group['completed'] else 'belum tersedia'
        median = f"{group['cost']['median_latency_ms']:.1f}" if group['completed'] else '—'
        p95 = f"{group['cost']['p95_latency_ms']:.1f}" if group['completed'] else '—'
        lines.append(f"| {group['model'].split('/')[-1]} | {group['config']} | "
                     f"{cell(group['mal_source_recall_proxy'])} | {cell(group['typ_assumed_benign_fpr'])} | "
                     f"{valid_cell} | {median} | {p95} |")
    lines.extend(['', 'Output tidak valid dihitung benign sesuai D18. Sensitivitas ketika output '
                  'tidak valid dihitung malicious, macro recall per kampanye, dan token tersedia '
                  'di `summary.json`. Error transport tidak dianggap prediksi.', '',
                  'Angka MAL mengukur kesesuaian terhadap label sumber, bukan recall terhadap '
                  'anotasi manusia. Tidak ada evaluasi HN atau klaim manfaat RAG; card KB belum '
                  'ditulis dan diverifikasi. Dataset ini belum memakai kuota dan cap kampanye '
                  'test final. Perbedaan model/config dilaporkan apa adanya tanpa penyetelan prompt.', '',
                  'Latency mencakup request awal, dengan prefix caching aktif; angka ini bukan '
                  'benchmark RQ4. Respons mentah, evidence, finish reason, token, dan latency '
                  'setiap panggilan tersedia dalam `results.jsonl`. Model, revisi, parameter, '
                  'dan checksum masukan tersedia dalam `protocol.json`.'])
    lines.extend(['', f"MAL mencakup {summary['mal_campaigns']} klaster operasional; klaster terbesar "
                  f"memuat {summary['largest_mal_campaign_count']}/873 pair. Macro recall memberi bobot "
                  'yang sama pada tiap klaster dan tersedia di bawah. Angka ini tetap memakai '
                  'label sumber dan definisi klaster §3.6, bukan validasi insiden independen.', '',
                  '| Model | Konfigurasi | Macro recall sumber per klaster |', '|---|---|---:|'])
    for group in groups:
        macro = group['mal_campaign_macro_recall_proxy']
        value = f'{100*macro:.2f}%' if macro is not None else 'belum tersedia'
        lines.append(f"| {group['model'].split('/')[-1]} | {group['config']} | {value} |")
    lines.extend(['', 'Diagnostik keluaran dan sensitivitas aturan invalid-as-malicious:', '',
                  '| Model | Konfigurasi | Batas 512 token | Invalid lainnya | MAL ditandai (sensitivitas) | FPR TYP (sensitivitas) |',
                  '|---|---|---:|---:|---:|---:|'])
    for group in groups:
        invalid = group['completed'] - group['json_valid']
        sensitivity = group['invalid_as_malicious']
        limited = str(group['length_limited']) if group['completed'] else '—'
        other = str(invalid - group['length_limited']) if group['completed'] else '—'
        lines.append(f"| {group['model'].split('/')[-1]} | {group['config']} | "
                     f"{limited} | {other} | "
                     f"{cell(sensitivity['mal'])} | {cell(sensitivity['typ'])} |")
    lines.extend(['', 'JSON valid berarti lolos parser dan skema runner serta tidak terpotong '
                  'karena batas token. Parser menerima objek JSON pertama dalam respons, '
                  'termasuk jika dibungkus Markdown; ini bukan persentase respons yang hanya '
                  'berisi JSON murni. Sensitivitas memakai respons yang sama, tanpa panggilan '
                  'ulang atau perubahan prompt.'])
    (directory / 'report.md').write_text('\n'.join(lines) + '\n')

    columns = ['model', 'config', 'completed', 'json_valid', 'mal_source_recall_proxy',
               'typ_assumed_benign_fpr', 'mal_campaign_macro_recall_proxy',
               'median_latency_ms', 'p95_latency_ms', 'mean_prompt_tokens',
               'mean_completion_tokens', 'complete_summary', 'human_annotation_verified']
    with (directory / 'summary.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for group in groups:
            writer.writerow({
                'model': group['model'], 'config': group['config'],
                'completed': group['completed'], 'json_valid': group['json_valid'],
                'mal_source_recall_proxy': group['mal_source_recall_proxy']['rate'],
                'typ_assumed_benign_fpr': group['typ_assumed_benign_fpr']['rate'],
                'mal_campaign_macro_recall_proxy': group['mal_campaign_macro_recall_proxy'],
                **group['cost'], 'complete_summary': summary['complete'],
                'human_annotation_verified': False})
