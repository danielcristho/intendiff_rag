# Perbandingan model — implementasi diff ber-ID, schema dan verifier

Status: belum lengkap; model belum selesai: Qwen/Qwen3-8B, microsoft/Phi-4-mini-instruct, meta-llama/Llama-3.1-8B-Instruct, ibm-granite/granite-3.3-8b-instruct

Setiap baris lengkap mencakup 873 MAL label sumber + 100 TYP diasumsikan benign. Invalid dihitung benign; sensitivitas ada di JSON.

| Model | Metode | Deteksi sumber | Alarm salah TYP | JSON valid |
|---|---|---:|---:|---:|
| Qwen/Qwen3-4B-Instruct-2507 | DIFF (ID) | 56.01% | 3.00% | 973/973 |
| Qwen/Qwen3-4B-Instruct-2507 | DIFF+I (ID) | 51.66% | 2.00% | 973/973 |
| Qwen/Qwen3-4B-Instruct-2507 | DIFF+I+verifier (ID) | 34.02% | 2.00% | 973/973 |
| Qwen/Qwen2.5-Coder-3B-Instruct | DIFF (ID) | 56.82% | 4.00% | 973/973 |
| Qwen/Qwen2.5-Coder-3B-Instruct | DIFF+I (ID) | 25.54% | 2.00% | 972/973 |
| Qwen/Qwen2.5-Coder-3B-Instruct | DIFF+I+verifier (ID) | 17.64% | 3.00% | 969/973 |
| Qwen/Qwen2.5-Coder-7B-Instruct | DIFF (ID) | 88.89% | 28.00% | 973/973 |
| Qwen/Qwen2.5-Coder-7B-Instruct | DIFF+I (ID) | 91.52% | 20.00% | 973/973 |
| Qwen/Qwen2.5-Coder-7B-Instruct | DIFF+I+verifier (ID) | 59.91% | 2.00% | 973/973 |

Verifier uses an additional IDS-I request per target. Its total cost is IDS-I plus VERIFY-I; labels are not human gold.
