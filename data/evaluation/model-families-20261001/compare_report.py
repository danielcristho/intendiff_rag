"""Write every completed comparison group to Markdown and CSV."""
import csv


def write_report(comparison, directory):
    groups = comparison['groups']
    lines = ['# Pembanding enam model lokal: Qwen, Phi, dan Llama', '',
        'Lengkap: 3.892 inferensi baru + 7.784 kontrol historis D82/D83. Semua memakai '
        '973 pair yang sama, output 2.048 token, BF16, dan konteks 32.768. '
        'Label sumber; bukan evaluasi gold atau uji hipotesis konfirmatori.', '',
        '| Model | Konfigurasi | Recall MAL sumber | FPR TYP | JSON valid | Terpotong | Macro recall kampanye |',
        '|---|---|---:|---:|---:|---:|---:|']
    for g in groups:
        lines.append(f"| {g['model'].split('/')[-1]} | {g['config']} | "
            f"{100*g['mal_source_recall_proxy']['rate']:.2f}% | "
            f"{100*g['typ_assumed_benign_fpr']['rate']:.2f}% | "
            f"{100*g['json_valid']/973:.2f}% | {g['length_limited']} | "
            f"{100*g['mal_campaign_macro_recall_proxy']:.2f}% |")
    lines.extend(['', 'Denominator per baris: 873 MAL, 100 TYP, dan 973 respons. Invalid dihitung benign. '
        'Sensitivitas invalid-as-malicious, token, dan latency tersedia dalam comparison.json.', '',
        '## Selisih terhadap setiap pembanding pada kelompok ukuran yang sama', '',
        '| Model baru | Kontrol historis | Konfigurasi | Δ recall (poin) | Δ FPR (poin) |',
        '|---|---|---|---:|---:|'])
    for c in comparison['comparisons']:
        lines.append(f"| {c['new_model'].split('/')[-1]} | {c['reference_model'].split('/')[-1]} | "
            f"{c['config']} | {c['subsets']['MAL']['delta_percentage_points']:+.2f} | "
            f"{c['subsets']['TYP']['delta_percentage_points']:+.2f} |")
    lines.extend(['', 'Phi-4-mini dan Llama-3.1 menggunakan template serta stop token native resmi. '
        'Prompt, parser, sampling, dan input dipertahankan. Kontrol Qwen historis tidak memakai '
        'override stop_token_ids; ini tercatat sebagai perbedaan native lintas keluarga.', '',
        'Kelompok A: 1≤P<5B; B: 5≤P<10B. Phi 3,836B dibandingkan dengan Qwen 3B/4B; '
        'Llama 8,030B dengan Qwen 7B/8B. Perbandingan tidak mengisolasi efek ukuran, '
        'post-training, data pelatihan, atau template chat.', '',
        'Kontrol Qwen memakai alokasi otomatis 0,65 (3B/4B) atau 0,80 (7B/8B). '
        'Model baru memakai KV cache eksplisit 6 GiB setelah kegagalan startup tanpa prediksi; '
        'pengaturan eksplisit ini menggantikan perhitungan cache dari alokasi 0,80. '
        'Latency antar-sesi bersifat observasional. Gold manusia, HN, RAG, cutoff temporal formal, '
        'dan Gate G1/G2 belum selesai. Tidak ada pemotongan input tambahan atau pemilihan '
        'pair berdasarkan prediksi.'])
    (directory / 'comparison.md').write_text('\n'.join(lines) + '\n')
    with (directory / 'comparison.csv').open('w', newline='') as stream:
        fields = ['model', 'config', 'completed', 'json_valid', 'length_limited', 'recall', 'fpr',
                  'macro_recall', 'median_latency_ms', 'p95_latency_ms']
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for g in groups:
            writer.writerow({**{k: g[k] for k in fields[:5]},
                'recall': g['mal_source_recall_proxy']['rate'], 'fpr': g['typ_assumed_benign_fpr']['rate'],
                'macro_recall': g['mal_campaign_macro_recall_proxy'],
                **{k: g['cost'][k] for k in fields[-2:]}})
