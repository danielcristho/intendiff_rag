import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  CATEGORY_IDS,
  HN_CATEGORIES,
  STATUSES,
  SUBSETS,
  type Filters,
} from "@/lib/audit";
import type { Subset } from "@/types/api";

// FilterBar selects which pairs are in the queue and steps through it.
export function FilterBar({
  filters,
  onChange,
  position,
  total,
  onMove,
}: {
  filters: Filters;
  onChange: (patch: Partial<Filters>) => void;
  position: number;
  total: number;
  onMove: (step: number) => void;
}) {
  // Clicking the active subset or category clears it, so one control both
  // applies and removes a filter.
  const toggle = <T,>(current: T | null, value: T) => (current === value ? null : value);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {STATUSES.map((status) => (
            <Button
              key={status}
              size="sm"
              variant={filters.status === status ? "solid" : "default"}
              onClick={() => onChange({ status })}
            >
              {status}
            </Button>
          ))}
          <span className="mx-1 h-5 w-px bg-hairline" />
          {SUBSETS.map((subset: Subset) => (
            <Button
              key={subset}
              size="sm"
              variant={filters.subset === subset ? "solid" : "default"}
              onClick={() => onChange({ subset: toggle(filters.subset, subset), category: null })}
            >
              {subset}
            </Button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-ink-faint">
            {total ? position + 1 : 0}/{total}
          </span>
          <Button size="sm" icon={<ChevronLeft className="h-4 w-4" />} onClick={() => onMove(-1)}>
            prev
          </Button>
          <Button size="sm" icon={<ChevronRight className="h-4 w-4" />} onClick={() => onMove(1)}>
            next
          </Button>
        </div>
      </div>

      {filters.subset === "HN" && (
        <div className="flex flex-wrap items-center gap-2">
          {CATEGORY_IDS.map((category) => (
            <Button
              key={category}
              size="sm"
              variant={filters.category === category ? "solid" : "default"}
              onClick={() => onChange({ category: toggle(filters.category, category) })}
            >
              {category}. {HN_CATEGORIES[category]}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
