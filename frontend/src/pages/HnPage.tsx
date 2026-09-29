import { useSearchParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";
import { CapabilityDelta } from "@/components/audit/CapabilityDelta";
import { DiffView } from "@/components/audit/DiffView";
import { IntentView } from "@/components/audit/IntentView";
import { QuotaBar } from "@/components/hn/QuotaBar";
import { VerifyForm } from "@/components/hn/VerifyForm";
import { useHnCandidate, useHnQueue, useVerifyHn } from "@/hooks/useHn";
import { errorMessage } from "@/lib/cards";
import { acceptedPerCategory, nextUnverified, npmUrl, quotaMet } from "@/lib/hn";
import { cn } from "@/lib/utils";

// HnPage walks the HN candidates in §3.3 order, path A first, until every category is full.
export function HnPage() {
  const [params, setParams] = useSearchParams();
  const queue = useHnQueue();
  const verify = useVerifyHn();
  const candidates = queue.data?.candidates ?? [];
  const verifications = queue.data?.verifications ?? {};
  const openId = params.get("id") ?? nextUnverified(candidates, verifications)?.id;
  const detail = useHnCandidate(openId);

  if (queue.isLoading) return <StateBlock>Memuat antrean HN…</StateBlock>;
  if (queue.isError) return <StateBlock tone="error">Gagal memuat: {String(queue.error)}</StateBlock>;
  if (!candidates.length)
    return (
      <StateBlock>
        Antrean kosong — jalankan <code className="font-mono">make hn-queue</code> setelah jalur A/B.
      </StateBlock>
    );

  const counts = acceptedPerCategory(verifications);
  const open = (id: string) => setParams({ id });
  const pair = detail.data;

  return (
    <div className="space-y-5">
      <QuotaBar counts={counts} />
      {quotaMet(verifications) && (
        <StateBlock>Kuota kelima kategori terpenuhi; verifikasi selesai.</StateBlock>
      )}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[260px_minmax(0,1fr)_320px]">
        <Card className="max-h-[80vh] overflow-y-auto p-3">
          {candidates.map((candidate) => {
            const entry = verifications[candidate.id];
            return (
              <button
                key={candidate.id}
                onClick={() => open(candidate.id)}
                className={cn(
                  "block w-full rounded px-2 py-1.5 text-left font-mono text-xs",
                  candidate.id === openId ? "bg-accent-soft text-accent" : "hover:bg-canvas",
                )}
              >
                <span className="text-ink-faint">{candidate.queue_position}.</span> {candidate.id}
                {entry && (
                  <span className={cn("ml-1", entry.decision === "accept" ? "text-ok" : "text-danger")}>
                    {entry.decision === "accept" ? `✓${entry.category}` : "✗"}
                  </span>
                )}
              </button>
            );
          })}
        </Card>

        <div className="min-w-0 space-y-5">
          {detail.isLoading && <StateBlock>Memuat kandidat…</StateBlock>}
          {pair && (
            <>
              <Card>
                <div className="font-mono text-sm font-semibold text-ink">{pair.id}</div>
                <div className="mt-0.5 font-mono text-xs text-ink-faint">
                  {pair.before} → {pair.after} · penerbit {pair.publisher ?? "?"}
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Badge value={pair.source} />
                  {(pair.categories ?? []).map((id) => <Badge key={id} value={`sinyal kategori ${id}`} />)}
                  {pair.truncated && <Badge value="truncated" />}
                </div>
                <a className="mt-2 inline-block text-xs text-accent underline" href={npmUrl(pair.name, pair.after ?? "")}
                  target="_blank" rel="noreferrer noopener">
                  Halaman npm versi ini
                </a>
                <p className="mt-1 text-xs text-ink-faint">
                  Jangan membuka URL yang tertulis di dalam kode sampel.
                </p>
              </Card>
              <Card>
                <h3 className="eyebrow">Intent (v_(t−1))</h3>
                <IntentView intent={pair.intent} />
                <CapabilityDelta item={pair} />
              </Card>
              <Card className="min-w-0">
                <h3 className="eyebrow">Smart-diff</h3>
                <DiffView diff={pair.diff} />
              </Card>
            </>
          )}
        </div>

        {openId && (
          <div className="space-y-3">
            <VerifyForm
              key={openId}
              current={verifications[openId]}
              busy={verify.isPending}
              onSubmit={(body) => verify.mutate({ id: openId, body })}
            />
            {verify.isError && <StateBlock tone="error">{errorMessage(verify.error)}</StateBlock>}
          </div>
        )}
      </div>
    </div>
  );
}
