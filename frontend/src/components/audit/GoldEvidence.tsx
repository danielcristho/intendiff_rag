import { useState } from "react";
import { parseGoldEvidence } from "@/lib/goldEvidence";
import type { Decision, Pair } from "@/types/api";

export function GoldEvidence({ pair, entry, onRecord }: {
  pair: Pair; entry: Decision; onRecord: (patch: Decision) => void;
}) {
  const [invalid, setInvalid] = useState(false);
  return (
    <div className="mt-5">
      <label className="eyebrow" htmlFor="gold-evidence">Gold evidence</label>
      <textarea
        id="gold-evidence"
        className="mt-2 w-full rounded border border-line bg-surface p-2 font-mono text-xs"
        rows={5}
        defaultValue={(entry.gold_evidence ?? []).join("\n")}
        placeholder="Copy malicious lines verbatim from the smart-diff, one per line."
        aria-invalid={invalid}
        onBlur={(event) => {
          const parsed = parseGoldEvidence(event.target.value, pair.diff);
          setInvalid(!parsed.valid);
          if (parsed.valid) onRecord({ gold_evidence: parsed.lines });
        }}
      />
      {invalid && <p role="alert" className="text-xs text-danger">Not saved: each evidence line must match the smart-diff exactly.</p>}
    </div>
  );
}
