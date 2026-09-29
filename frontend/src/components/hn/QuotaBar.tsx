import { HN_CATEGORIES } from "@/lib/audit";
import { QUOTA } from "@/lib/hn";
import { cn } from "@/lib/utils";

// QuotaBar shows how many candidates each category has accepted against its quota.
export function QuotaBar({ counts }: { counts: Record<number, number> }) {
  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-5">
      {Object.entries(HN_CATEGORIES).map(([id, name]) => {
        const count = counts[Number(id)] ?? 0;
        return (
          <div key={id} className="rounded bg-surface p-3 shadow-card">
            <div className="truncate text-xs text-ink-faint" title={name}>
              {id}. {name}
            </div>
            <div className={cn("mt-1 font-mono text-sm", count >= QUOTA ? "text-ok" : "text-ink")}>
              {count}/{QUOTA}
            </div>
            <div className="mt-1 h-1 rounded bg-canvas">
              <div
                className={cn("h-1 rounded", count >= QUOTA ? "bg-ok" : "bg-accent")}
                style={{ width: `${Math.min(100, (count / QUOTA) * 100)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
