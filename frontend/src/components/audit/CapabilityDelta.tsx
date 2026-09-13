import { describeEvidence } from "@/lib/audit";
import type { Pair } from "@/types/api";

// CapabilityDelta shows the retrieval key and, when present, why each signal fired.
//
// The evidence matters for §3.3: a hard negative is categorised by its
// documented purpose, so an annotator has to reach the triggering line rather
// than hunt for it in a smart-diff that can run to 28k tokens.
export function CapabilityDelta({ pair }: { pair: Pair }) {
  if (!pair.delta?.length) return null;

  return (
    <>
      <h3 className="eyebrow mt-5">Capability delta</h3>
      <div className="space-y-2">
        {pair.delta.map((signal) => {
          const evidence = pair.delta_evidence?.[signal] ?? [];
          return (
            <div key={signal}>
              <code className="block rounded bg-canvas px-2 py-1 font-mono text-xs">{signal}</code>
              {evidence.map((entry, i) => (
                <div
                  key={i}
                  className="mt-1 break-all border-l-2 border-hairline pl-2 font-mono text-[11px] text-ink-faint"
                >
                  {describeEvidence(entry)}
                </div>
              ))}
            </div>
          );
        })}
      </div>
      <p className="mt-2 text-xs text-ink-faint">
        Hanya kunci retrieval — tidak pernah ditampilkan ke model (D25).
      </p>
    </>
  );
}
