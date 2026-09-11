import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { api } from "@/services/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, StateBlock } from "@/components/ui/card";
import { DiffView } from "@/components/audit/DiffView";
import { ERRORS, FILTERS, VERDICTS, keep, type Filter } from "@/lib/audit";
import type { Decision, ErrorClass, Verdict } from "@/types/api";

export function AuditPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<Filter>("semua");
  const [cursor, setCursor] = useState(0);

  const pairsQuery = useQuery({ queryKey: ["pairs"], queryFn: api.pairs });
  const decisionsQuery = useQuery({ queryKey: ["decisions"], queryFn: api.decisions });

  const save = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Decision }) => api.saveDecision(id, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["decisions"] }),
  });

  const decisions = decisionsQuery.data ?? {};
  const shown = useMemo(
    () => (pairsQuery.data?.pairs ?? []).filter((p) => keep(p, decisions, filter)),
    [pairsQuery.data, decisions, filter],
  );

  // Daftar menyusut saat filter "belum direview" dipakai, jadi cursor dijepit
  // ke rentang yang masih ada alih-alih menabrak index kosong.
  const index = shown.length ? Math.min(cursor, shown.length - 1) : 0;
  const pair = shown[index];
  const entry: Decision = pair ? (decisions[pair.id] ?? {}) : {};

  const move = (step: number) =>
    setCursor((c) => Math.min(Math.max(c + step, 0), Math.max(shown.length - 1, 0)));

  const record = (patch: Decision) => {
    if (!pair) return;
    save.mutate({ id: pair.id, patch });
    if (patch.label) move(1);
  };

  useEffect(() => {
    const keys: Record<string, () => void> = {
      m: () => record({ label: "malicious" }),
      b: () => record({ label: "benign" }),
      s: () => record({ label: "skip" }),
      ArrowLeft: () => move(-1),
      ArrowRight: () => move(1),
    };
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") return;
      const fn = keys[e.key];
      if (fn) {
        e.preventDefault();
        fn();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (pairsQuery.isLoading) return <StateBlock>Memuat pasangan…</StateBlock>;
  if (pairsQuery.isError)
    return <StateBlock tone="error">Gagal memuat: {String(pairsQuery.error)}</StateBlock>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          {FILTERS.map((f) => (
            <Button
              key={f}
              size="sm"
              variant={filter === f ? "solid" : "default"}
              onClick={() => {
                setFilter(f);
                setCursor(0);
              }}
            >
              {f}
            </Button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-ink-faint">
            {shown.length ? index + 1 : 0}/{shown.length}
          </span>
          <Button size="sm" variant="default" icon={<ChevronLeft className="h-4 w-4" />} onClick={() => move(-1)}>
            prev
          </Button>
          <Button size="sm" variant="default" icon={<ChevronRight className="h-4 w-4" />} onClick={() => move(1)}>
            next
          </Button>
        </div>
      </div>

      {!pair ? (
<StateBlock>Tidak ada pair pada filter &quot;{filter}&quot;.</StateBlock>
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[380px_1fr]">
          <div className="space-y-5">
            <Card>
              <div className="font-mono text-sm font-semibold text-ink">{pair.name}</div>
              <div className="mt-0.5 font-mono text-xs text-ink-faint">
                {pair.before ?? "?"} → {pair.after ?? "?"}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {pair.label && <Badge value={`gold ${pair.label}`} />}
                {pair.pred && <Badge value={`pred ${pair.pred}`} />}
                {entry.label && <Badge value={entry.label} />}
                {entry.error && <Badge value={entry.error} />}
              </div>
            </Card>

            <Card>
              <h3 className="eyebrow">Intent</h3>
              <p className="text-sm">
                {pair.intent ?? <span className="italic text-ink-faint">belum ada intent profile</span>}
              </p>
              {pair.delta?.length ? (
                <>
                  <h3 className="eyebrow mt-5">
                    Capability delta
                  </h3>
                  <div className="space-y-1">
                    {pair.delta.map((d) => (
                      <code key={d} className="block rounded bg-canvas px-2 py-1 font-mono text-xs">
                        {d}
                      </code>
                    ))}
                  </div>
                </>
              ) : null}
            </Card>

            <Card>
              <h3 className="eyebrow">
                Verdict <span className="font-mono normal-case text-ink-faint">(m / b / s)</span>
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {VERDICTS.map((v: Verdict) => (
                  <Button
                    key={v}
                    size="sm"
                    variant={entry.label === v ? "solid" : "default"}
                    onClick={() => record({ label: v })}
                  >
                    {v}
                  </Button>
                ))}
              </div>

              {pair.pred && (
                <>
                  <h3 className="eyebrow mt-5">
                    Error taxonomy
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    {ERRORS.map((e: ErrorClass) => (
                      <Button
                        key={e}
                        size="sm"
                        variant={entry.error === e ? "solid" : "default"}
                        onClick={() => record({ error: e })}
                      >
                        {e}
                      </Button>
                    ))}
                  </div>
                </>
              )}

              <textarea
                className="mt-4 w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                rows={3}
                placeholder="Catatan…"
                defaultValue={entry.note ?? ""}
                key={pair.id}
                onBlur={(e) => record({ note: e.target.value })}
              />
            </Card>
          </div>

          <Card className="min-w-0">
            <h3 className="eyebrow">Smart-diff</h3>
            <DiffView diff={pair.diff} />
          </Card>
        </div>
      )}
    </div>
  );
}
