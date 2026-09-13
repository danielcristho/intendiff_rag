# Deploy ke mesin GPU

Mesin `gpu-host` dipakai bersama produksi. Dua hal di bawah lebih penting
daripada urutan perintahnya.

## Sebelum apa pun: dua risiko

**1. vLLM bisa mematikan layanan produksi.** vLLM mem-pra-alokasi
`--gpu-memory-utilization` dari **total** memori GPU, bukan dari yang tersisa.
Pada nilai default 0,9 ia mengambil ~11 GiB dari kartu 12 GiB, dan
`production-service` yang jalan di kartu yang sama akan kehabisan memori.

Cek dulu yang benar-benar bebas, dengan yolo sedang hidup:

```
nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv
```

Lalu setel `VLLM_GPU_UTIL` di bawah angka itu. Untuk konteks: Qwen2.5-Coder-3B
butuh ~6,9 GiB dan Qwen3-4B ~11,95 GiB (D44). Kalau yang bebas kurang dari itu,
**jangan paksakan** — jadwalkan jendela saat yolo dimatikan, atau pakai mesin
lain (D45 opsi A).

**2. UI audit tidak punya autentikasi.** Port di-publish ke `0.0.0.0`, jadi
siapa pun yang bisa mencapai host itu bisa membaca dan mengubah label
penelitian. Tidak ada login, tidak ada token.

Kalau mau lebih rapat tanpa kehilangan akses jarak jauh, setel `BIND_ADDR` di
`.env` ke alamat VPN mesin itu:

```
BIND_ADDR=192.0.2.11
```

Itu mengikuti cara container lain di host ini di-publish, dan menjauhkan port
dari LAN. `BIND_ADDR=127.0.0.1` menutupnya sama sekali, lalu diakses lewat
`ssh -L 5174:localhost:5174 <user>@<gpu-host>`.

## Langkah

```bash
# 1. Ambil kode
git clone git@github.com:danielcristho/intendiff_rag.git
cd intendiff_rag

# 2. Konfigurasi
cp .env.example .env
sed -i "s/^APP_UID=.*/APP_UID=$(id -u)/; s/^APP_GID=.*/APP_GID=$(id -g)/" .env

# 3. Pastikan portnya masih bebas di mesin ini
docker ps --format '{{.Names}}\t{{.Ports}}'

# 4. Jalankan UI audit (tanpa GPU)
docker compose up -d --build backend frontend
curl localhost:8100/health          # -> ok
```

Akses UI dari laptop: buka `http://<host>:5174`.

Tiap anotator mengisi namanya sendiri di gerbang identitas, dan keputusannya
tersimpan terpisah di `data/audit_decisions.<nama>.json`.

## Model server (hanya saat menjalankan eksperimen)

```bash
# Baca ulang peringatan di atas lebih dulu.
docker compose --profile model up -d vllm
docker compose logs -f vllm            # tunggu "Application startup complete"

python pipeline/runner.py --model Qwen/Qwen2.5-Coder-3B-Instruct
# --base-url sudah default ke http://localhost:8101

docker compose --profile model down    # lepaskan GPU begitu selesai
```

vLLM sengaja tidak punya `restart:` — reboot tidak boleh diam-diam merebut GPU.

## Data

`./data` di-bind ke container dan berisi satu-satunya salinan label penelitian
kalian. Itu artefak yang tidak bisa dibuat ulang: `audit_decisions.*.json` ada
di `.gitignore`, jadi tidak ikut ter-push.

```bash
tar czf ~/audit-backup-$(date +%F).tar.gz data/
```

Backup sebelum Gate G1, dan sesudah tiap sesi pelabelan panjang.

## Pembaruan

```bash
git pull
docker compose up -d --build backend frontend
```

Container backend dan frontend stateless; seluruh state ada di `./data`.
