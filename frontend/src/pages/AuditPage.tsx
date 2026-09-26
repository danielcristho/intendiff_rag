import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";
import { DecisionPanel } from "@/components/audit/DecisionPanel";
import { CapabilityDelta } from "@/components/audit/CapabilityDelta";
import { DiffView } from "@/components/audit/DiffView";
import { FilterBar } from "@/components/audit/FilterBar";
import { IntentView } from "@/components/audit/IntentView";
import { ModelOutput } from "@/components/audit/ModelOutput";
import { useDecisions, usePairs, useSaveDecision } from "@/hooks/useAuditData";
import { NO_FILTER, keep, type Filters } from "@/lib/audit";
import type { Decision } from "@/types/api";

// Consts
const VERDICT_KEYS: Record<string, Decision> = {
  m: { label: "malicious" },
  b: { label: "benign" },
  s: { label: "skip" },
};

// AuditPage walks the filtered queue of pairs and records one verdict each.
export function AuditPage() {
  const [filters, setFilters] = useState<Filters>(NO_FILTER);
  const [cursor, setCursor] = useState(0);

  const pairsQuery = usePairs();
  const decisionsQuery = useDecisions();
  const save = useSaveDecision();

  const decisions = decisionsQuery.data ?? {};
  const queue = useMemo(
    () => (pairsQuery.data?.pairs ?? []).filter((pair) => keep(pair, decisions, filters)),
    [pairsQuery.data, decisions, filters],
  );

  // The queue shrinks as filters change, so clamp the cursor into what is left
  // rather than letting it run off the end.
  const position = queue.length ? Math.min(cursor, queue.length - 1) : 0;
  const pair = queue[position];
  const entry: Decision = pair ? (decisions[pair.id] ?? {}) : {};

  const move = (step: number) =>
    setCursor((current) => Math.min(Math.max(current + step, 0), Math.max(queue.length - 1, 0)));

  // record advances only on a verdict, so editing a category or note stays put.
  const record = (patch: Decision) => {
    if (!pair) return;
    save.mutate({ id: pair.id, patch });
    if (patch.label) move(1);
  };

  const applyFilters = (patch: Partial<Filters>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setCursor(0);
  };

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.tagName === "TEXTAREA" || target.tagName === "INPUT") return;

      const verdict = VERDICT_KEYS[event.key];
      const step = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
      if (!verdict && !step) return;

      event.preventDefault();
      if (verdict) record(verdict);
      else move(step);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (pairsQuery.isLoading) return <StateBlock>Memuat pasangan…</StateBlock>;
  if (pairsQuery.isError)
    return <StateBlock tone="error">Gagal memuat: {String(pairsQuery.error)}</StateBlock>;

  return (
    <div className="space-y-5">
      <FilterBar
        filters={filters}
        onChange={applyFilters}
        position={position}
        total={queue.length}
        onMove={move}
      />

      {!pair ? (
        <StateBlock>Tidak ada pair pada filter ini.</StateBlock>
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[380px_1fr]">
          <div className="space-y-5">
            <Card>
              <div className="font-mono text-sm font-semibold text-ink">{pair.name}</div>
              <div className="mt-0.5 font-mono text-xs text-ink-faint">
                {pair.before ?? "?"} → {pair.after ?? "?"}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {pair.subset && <Badge value={pair.subset} />}
                {pair.truncated && <Badge value="truncated" />}
                {pair.label && <Badge value={`gold ${pair.label}`} />}
                {pair.pred && <Badge value={`pred ${pair.pred}`} />}
                {entry.label && <Badge value={entry.label} />}
                {entry.error && <Badge value={entry.error} />}
              </div>
            </Card>

            <Card>
              <h3 className="eyebrow">Intent</h3>
              <IntentView intent={pair.intent} />
              <CapabilityDelta item={pair} />
            </Card>

            <DecisionPanel pair={pair} entry={entry} onRecord={record} />
          </div>

          <div className="min-w-0 space-y-5">
            <Card className="min-w-0">
              <h3 className="eyebrow">Smart-diff</h3>
              <DiffView diff={pair.diff} />
            </Card>
            <ModelOutput pair={pair} />
          </div>
        </div>
      )}
    </div>
  );
}
