import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";
import { useAnnotator } from "@/components/AnnotatorGate";
import { useAnnotators, useDecisions, usePairs } from "@/hooks/useAuditData";
import { SUBSETS, summarize } from "@/lib/audit";
import { formatPct } from "@/lib/utils";
import type { Subset } from "@/types/api";

// GATE_G1 is the per-subset target and minimum Gate G1 is judged against (§3).
const GATE_G1: Record<Subset, { target: number; min: number }> = {
  MAL: { target: 50, min: 40 },
  HN: { target: 100, min: 75 },
  TYP: { target: 100, min: 100 },
};

// Stat is a single headline number with an optional caption.
function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <div className="eyebrow mb-1">{label}</div>
      <div className="font-mono text-2xl font-semibold text-ink">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-ink-faint">{hint}</div>}
    </Card>
  );
}

// OverviewPage reports labelling progress for the signed-in annotator.
export function OverviewPage() {
  const { annotator } = useAnnotator();
  const pairsQuery = usePairs();
  const decisionsQuery = useDecisions();
  const annotatorsQuery = useAnnotators();

  if (pairsQuery.isLoading || decisionsQuery.isLoading) return <StateBlock>Memuat…</StateBlock>;
  if (pairsQuery.isError)
    return <StateBlock tone="error">Gagal memuat: {String(pairsQuery.error)}</StateBlock>;

  const summary = summarize(pairsQuery.data?.pairs ?? [], decisionsQuery.data ?? {});

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg">Progres label audit</h1>
        <p className="mt-0.5 font-mono text-xs text-ink-faint">
          anotator: {annotator} · sumber: {pairsQuery.data?.source}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat
          label="Direview"
          value={`${summary.reviewed}/${summary.total}`}
          hint={formatPct(summary.total ? summary.reviewed / summary.total : 0)}
        />
        <Stat label="Malicious" value={String(summary.byLabel.malicious)} />
        <Stat label="Benign" value={String(summary.byLabel.benign)} />
        <Stat
          label="Skip / ragu"
          value={String(summary.byLabel.skip)}
          hint="perlu adjudikasi berdua"
        />
      </div>

      <Card>
        <h2 className="eyebrow">Per subset — Gate G1</h2>
        {summary.total === 0 ? (
          <StateBlock>Belum ada pair. Dataset asli menyusul di M1–2.</StateBlock>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-ink-faint">
                <th className="pb-2 font-medium">Subset</th>
                <th className="pb-2 font-medium">Direview</th>
                <th className="pb-2 font-medium">Terkumpul</th>
                <th className="pb-2 font-medium">Target / minimum</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {SUBSETS.map((subset) => {
                const row = summary.bySubset[subset];
                const gate = GATE_G1[subset];
                return (
                  <tr key={subset} className="border-t border-hairline">
                    <td className="py-1.5">{subset}</td>
                    <td className="py-1.5">{row.reviewed}</td>
                    <td className={row.total < gate.min ? "py-1.5 text-warn" : "py-1.5"}>
                      {row.total}
                    </td>
                    <td className="py-1.5 text-ink-faint">
                      {gate.target} / {gate.min}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      <Card>
        <h2 className="eyebrow">Anotator</h2>
        <p className="mb-3 text-xs text-ink-faint">
          Hanya jumlah keputusan — label anotator lain tidak ditampilkan supaya pelabelan tetap
          independen (§8).
        </p>
        {annotatorsQuery.data?.length ? (
          <div className="space-y-1 font-mono text-sm">
            {annotatorsQuery.data.map((row) => (
              <div
                key={row.annotator}
                className="flex justify-between border-t border-hairline py-1.5"
              >
                <span>
                  {row.annotator}
                  {row.annotator === annotator && <span className="ml-2 text-ink-faint">(kamu)</span>}
                </span>
                <span>{row.count}</span>
              </div>
            ))}
          </div>
        ) : (
          <StateBlock>Belum ada keputusan tersimpan.</StateBlock>
        )}
      </Card>

      <Card>
        <h2 className="eyebrow">Error taxonomy</h2>
        {summary.disagreements === 0 ? (
          <StateBlock>
            Belum ada prediksi model — bagian ini terisi setelah eksperimen M5–6 jalan.
          </StateBlock>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(summary.byError).map(([name, count]) => (
              <div key={name}>
                <div className="font-mono text-xl font-semibold text-ink">{count}</div>
                <div className="text-xs text-ink-faint">{name} error</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
