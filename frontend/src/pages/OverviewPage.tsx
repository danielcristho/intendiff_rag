import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card, StateBlock } from "@/components/ui/card";
import { summarize } from "@/lib/audit";
import { formatPct } from "@/lib/utils";

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <div className="eyebrow mb-1">{label}</div>
      <div className="font-mono text-2xl font-semibold text-ink">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-ink-faint">{hint}</div>}
    </Card>
  );
}

export function OverviewPage() {
  const pairs = useQuery({ queryKey: ["pairs"], queryFn: api.pairs });
  const decisions = useQuery({ queryKey: ["decisions"], queryFn: api.decisions });

  if (pairs.isLoading || decisions.isLoading) return <StateBlock>Memuat…</StateBlock>;
  if (pairs.isError) return <StateBlock tone="error">Gagal memuat: {String(pairs.error)}</StateBlock>;

  const s = summarize(pairs.data?.pairs ?? [], decisions.data ?? {});

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg">Progres label audit</h1>
        <p className="mt-0.5 font-mono text-xs text-ink-faint">sumber: {pairs.data?.source}</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat
          label="Direview"
          value={`${s.reviewed}/${s.total}`}
          hint={formatPct(s.total ? s.reviewed / s.total : 0)}
        />
        <Stat label="Malicious" value={String(s.byLabel.malicious)} />
        <Stat label="Benign" value={String(s.byLabel.benign)} />
        <Stat label="Skip / ragu" value={String(s.byLabel.skip)} hint="perlu adjudikasi berdua" />
      </div>

      <Card>
        <h2 className="eyebrow">Error taxonomy</h2>
        {s.disagreements === 0 ? (
          <StateBlock>
            Belum ada prediksi model — bagian ini terisi setelah eksperimen M5–6 jalan.
          </StateBlock>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(s.byError).map(([k, v]) => (
              <div key={k}>
                <div className="font-mono text-xl font-semibold text-ink">{v}</div>
                <div className="text-xs text-ink-faint">{k} error</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
