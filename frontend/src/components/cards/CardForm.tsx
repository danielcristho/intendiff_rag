import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { MAX_EXCERPT_LINES } from "@/lib/cards";
import type { CardText } from "@/types/api";

// Hints paraphrase methodology §5.1; the budgets are enforced again by pipeline/promote.py.
const FIELDS: { key: keyof CardText; label: string; hint: string; rows: number; mono?: boolean }[] = [
  { key: "intent", label: "intent", hint: "Tujuan paket yang diklaim, satu kalimat, ≤ 64 token.", rows: 2 },
  {
    key: "behavior_chain",
    label: "behavior_chain",
    hint: "Rantai perilaku, misal: install hook → read whole environment → HTTPS POST to hard-coded host",
    rows: 2,
  },
  {
    key: "code_excerpt",
    label: "code_excerpt",
    hint: `≤ ${MAX_EXCERPT_LINES} baris verbatim — pilih dari panel sampel, jangan diketik ulang.`,
    rows: 8,
    mono: true,
  },
  {
    key: "rationale",
    label: "rationale",
    hint: "≤ 2 kalimat: trigger, data beserta tujuannya, dan hubungannya dengan intent.",
    rows: 3,
  },
];

// CardForm edits the four text fields of one card, in English.
export function CardForm({
  text,
  editable,
  busy,
  onChange,
  onSave,
}: {
  text: CardText;
  editable: boolean;
  busy: boolean;
  onChange: (patch: Partial<CardText>) => void;
  onSave: (submit: boolean) => void;
}) {
  const excerptLines = text.code_excerpt ? text.code_excerpt.split("\n").length : 0;
  return (
    <Card>
      <h3 className="eyebrow">Teks card (bahasa Inggris)</h3>
      <div className="space-y-4">
        {FIELDS.map(({ key, label, hint, rows, mono }) => (
          <label key={key} className="block">
            <span className="font-mono text-xs font-semibold text-ink">{label}</span>
            {key === "code_excerpt" && (
              <span
                className={`ml-2 text-xs ${excerptLines > MAX_EXCERPT_LINES ? "text-danger" : "text-ink-faint"}`}
              >
                {excerptLines}/{MAX_EXCERPT_LINES} baris
              </span>
            )}
            <textarea
              rows={rows}
              readOnly={!editable}
              value={text[key]}
              onChange={(event) => onChange({ [key]: event.target.value })}
              className={`mt-1 w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent read-only:border-hairline read-only:bg-canvas ${mono ? "whitespace-pre font-mono text-xs" : ""}`}
            />
            <span className="text-xs text-ink-faint">{hint}</span>
          </label>
        ))}
      </div>
      {editable && (
        <div className="mt-4 flex gap-2">
          <Button disabled={busy} onClick={() => onSave(false)}>
            Simpan draf
          </Button>
          <Button variant="solid" disabled={busy} onClick={() => onSave(true)}>
            Kirim untuk dicek
          </Button>
        </div>
      )}
    </Card>
  );
}
