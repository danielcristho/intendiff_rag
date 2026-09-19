import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";
import { Badge } from "@/components/ui/badge";
import { useResults } from "@/hooks/useAuditData";
import type { ModelResult, Pair } from "@/types/api";

function agreement(result: ModelResult, gold?: string) {
  if (!gold || !result.verdict) return null;
  return result.verdict.toLowerCase() === gold.toLowerCase() ? "✓" : "✗";
}

// ModelOutput shows what each configuration was given and what it answered.
//
// The retrieved cards are the point: "retrieval error" in the EA4 taxonomy
// cannot be judged without seeing which cards reached the prompt and where.
export function ModelOutput({ pair }: { pair: Pair }) {
  const results = useResults(pair.id);
  const rows = results.data ?? [];

  if (results.isLoading) return null;

  return (
    <Card className="min-w-0">
      <h3 className="eyebrow">Model output</h3>
      {rows.length === 0 ? (
        <StateBlock>
          Belum ada run untuk pair ini — terisi setelah eksperimen M5–6 jalan.
        </StateBlock>
      ) : (
        <div className="space-y-3">
          {rows.map((row) => (
            <div key={row.run_key} className="border-t border-hairline pt-3 first:border-0 first:pt-0">
              <div className="flex flex-wrap items-center gap-2">
                <code className="font-mono text-xs font-semibold text-ink">{row.config}</code>
                {row.verdict ? <Badge value={row.verdict} /> : <Badge value="invalid" />}
                <span className="font-mono text-xs text-ink-faint">
                  {agreement(row, pair.label)} · {row.latency_ms} ms ·{" "}
                  {row.prompt_tokens ?? "?"}+{row.completion_tokens ?? "?"} tok
                </span>
              </div>

              {row.cards.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {row.cards.map((card) => (
                    <span
                      key={card.id}
                      className="rounded bg-canvas px-1.5 py-0.5 font-mono text-[11px] text-ink-soft"
                    >
                      #{card.position} {card.label} · {card.id} · {card.score}
                    </span>
                  ))}
                </div>
              )}

              {row.reason && <p className="mt-1.5 text-xs">{row.reason}</p>}
              {row.evidence?.length ? (
                <div className="mt-1 space-y-0.5">
                  {row.evidence.map((line, i) => (
                    <code
                      key={i}
                      className="block break-all border-l-2 border-hairline pl-2 font-mono text-[11px] text-ink-faint"
                    >
                      {line}
                    </code>
                  ))}
                </div>
              ) : null}
              {row.error && <p className="mt-1 text-xs text-danger">{row.error}</p>}

              {row.raw && (
                <details className="mt-1.5">
                  <summary className="cursor-pointer font-mono text-[11px] text-ink-faint">
                    raw
                  </summary>
                  <pre className="mt-1 overflow-x-auto rounded bg-canvas p-2 font-mono text-[11px]">
                    {row.raw}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
