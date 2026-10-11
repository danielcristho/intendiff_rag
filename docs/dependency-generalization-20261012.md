# D89 — kontrol konteks dependency pada kandidat lintas nama

Kelanjutan D88, ditetapkan sebelum inferensi pada 12 Oktober 2026. Tujuannya
memeriksa perubahan alarm saat isi dependency ditambahkan dengan instruksi
kondisional yang sama. Ini eksplorasi dev; bukan pengujian hipotesis MM/MB.

## Seleksi sebelum prediksi

Pool adalah 1.157 pair praproses-v2. Hanya MAL/HN, diff tidak terpotong,
dan dependency yang tercatat pada delta_evidence.dependency_change. Tidak
membaca hasil model untuk seleksi. Target dengan penambahan easy-day-js
seluruhnya dikeluarkan agar tidak memperbanyak keluarga D88. Ketiadaan sebuah
nama dalam metadata extractor tidak berarti dependency itu tidak berubah.

Cocokkan deklarasi ke arsip lokal inventory Datadog dan extracted.typical,
menggunakan npm semver yang sudah terpasang, tanpa mengeksekusi kode sampel.
Audit ketersediaan awal: 67 kombinasi target–versi (64 HN, 3 MAL), sebelum
pemeriksaan tanggal. Semua tiga kombinasi MAL berasal dari zuper-cli/axios.
Jadi ketersediaan ini belum mendukung klaim lintas keluarga serangan.

Timestamp target/dependency diambil dari field time registry npm resmi;
64 respons diproyeksikan ke timestamp, identitas, URL sumber, waktu pengambilan,
dan hash respons. Ini metadata registry saat diperiksa, bukan bukti instalasi.
Versi yang terbit setelah target atau tanpa timestamp dikeluarkan. Untuk tiap
pair–nama dependency, pilih snapshot lokal yang terbit paling akhir sebelum/bersamaan
target dan cocok rentang (tie: string versi). Ini bukan resolver seluruh registry.
Nama dependency sama dengan target dikeluarkan (self-reference).

Isi konteks: manifest utuh, satu main/exports entrypoint, serta file hook
preinstall/install/postinstall yang dapat diidentifikasi sebagai perintah node
sederhana. Tidak mengikuti import/requires atau seluruh tree. Perintah kompleks,
file hilang/keluar root, file >200.000 byte, atau konteks melebihi 32.768 dengan
cadangan output 2.048 dikeluarkan; tanpa memotong atau mencoba versi lain setelah
versi terpilih gagal. Byte berkas dicocokkan ke arsip lokal sebelum dipakai.

Dari kandidat yang lolos, urut SHA-256 D89|nama-dependency lalu D89|pair-id;
ambil maksimal satu target per nama dependency dan nama target, tanpa kuota hasil
MAL/HN. Seluruh kandidat/gugur dan alasannya disimpan. Nama dependency berbeda
belum membuktikan keluarga kode/insiden independen. Paparan D85/D86 serta MAL
historis dicatat. Seluruh target diperlakukan sebagai dev dan dikecualikan dari
KB/test mendatang; tidak diklaim sebagai holdout baru.

## Dua kondisi baru

- NO-SOURCE: diff+intent IDS-I, instruksi asumsi nama/versi/section dependency,
  tanpa isi berkas dependency.
- WITH-SOURCE: pesan yang sama, mengganti penanda tidak tersedianya berkas dengan
  isi konteks ber-ID. Label keamanan dan metadata seleksi tidak masuk prompt.

Keduanya merupakan penilaian bersyarat; tidak menyatakan versi terpasang diketahui.
Urutan arm dibalik untuk pair dengan hash ganjil, lalu dijalankan serial.
Tidak ada perubahan prompt di tengah batch. Snapshot model/runtime/decoder sama
D88: Qwen3-4B, BF16, seed 0, temperature 0, top_p 1, output 2.048, konteks 32.768,
KV 6 GiB, satu sequence, prefix caching, generation-config vllm.
Tanpa warmup generasi, retry otomatis, atau truncation tambahan.

Metrik: jumlah verdict malicious/benign/invalid per cohort dan arm, transisi,
JSON/length/unknown-ID, kutipan isi dependency, token dan latensi sesi. HN masih
pending sehingga alarm tidak disebut FPR. Satu target MAL tidak mendukung estimasi
recall lintas serangan. Tidak ada uji signifikansi, gold manusia, atau hasil RAG.
Konteks bisa memuat kode netral pada target MAL; label target tidak dilimpahkan
ke dependency. Semua hasil termasuk nol perubahan disimpan.
