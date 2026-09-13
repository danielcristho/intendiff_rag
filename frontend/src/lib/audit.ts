import type { Decisions, DeltaEvidence, ErrorClass, Pair, Subset, Verdict } from "@/types/api";

// STATUSES are the review-progress filters offered in the queue.
export const STATUSES = ["semua", "belum direview", "beda dari gold"] as const;
// Status is one review-progress filter.
export type Status = (typeof STATUSES)[number];
// SUBSETS lists the test-set subsets in reporting order.
export const SUBSETS: Subset[] = ["MAL", "HN", "TYP"];
// VERDICTS lists the verdicts an annotator can record.
export const VERDICTS: Verdict[] = ["malicious", "benign", "skip"];
// ERRORS lists the EA4 error classes.
export const ERRORS: ErrorClass[] = ["capability", "intent", "retrieval"];

// HN_CATEGORIES names the five hard-negative categories of methodology §3.3.
export const HN_CATEGORIES: Record<number, string> = {
  1: "Process execution & tooling",
  2: "Telemetry",
  3: "Licensing",
  4: "Network, scraper, unduhan",
  5: "Deprecation & perubahan struktur",
};

// CATEGORY_IDS lists the hard-negative category numbers in order.
export const CATEGORY_IDS = Object.keys(HN_CATEGORIES).map(Number);

// Filters is the combination of review status, subset and category in effect.
export interface Filters {
  status: Status;
  subset: Subset | null;
  category: number | null;
}

// NO_FILTER is the filter state that admits every pair.
export const NO_FILTER: Filters = { status: "semua", subset: null, category: null };

// keep reports whether a pair survives every active filter.
export function keep(pair: Pair, decisions: Decisions, filters: Filters): boolean {
  if (filters.subset && pair.subset !== filters.subset) return false;
  if (filters.category != null && pair.category !== filters.category) return false;
  if (filters.status === "belum direview") return !decisions[pair.id];
  if (filters.status === "beda dari gold") return Boolean(pair.pred) && pair.pred !== pair.label;
  return true;
}

// Summary is the labelling progress shown on the overview page.
export interface Summary {
  total: number;
  reviewed: number;
  byLabel: Record<Verdict, number>;
  byError: Record<ErrorClass, number>;
  bySubset: Record<Subset, { total: number; reviewed: number }>;
  disagreements: number;
}

// summarize counts progress per verdict, per error class, and per subset.
export function summarize(pairs: Pair[], decisions: Decisions): Summary {
  const byLabel = { malicious: 0, benign: 0, skip: 0 } as Record<Verdict, number>;
  const byError = { capability: 0, intent: 0, retrieval: 0 } as Record<ErrorClass, number>;
  const bySubset = {
    MAL: { total: 0, reviewed: 0 },
    HN: { total: 0, reviewed: 0 },
    TYP: { total: 0, reviewed: 0 },
  } as Record<Subset, { total: number; reviewed: number }>;
  let reviewed = 0;

  for (const pair of pairs) {
    const decision = decisions[pair.id];
    const subset = pair.subset ? bySubset[pair.subset] : undefined;
    if (subset) subset.total += 1;
    if (!decision) continue;
    reviewed += 1;
    if (subset) subset.reviewed += 1;
    if (decision.label) byLabel[decision.label] += 1;
    if (decision.error) byError[decision.error] += 1;
  }

  return {
    total: pairs.length,
    reviewed,
    byLabel,
    byError,
    bySubset,
    disagreements: pairs.filter((pair) =>
      keep(pair, decisions, { ...NO_FILTER, status: "beda dari gold" }),
    ).length,
  };
}

// describeEvidence renders one piece of delta evidence as a single line.
export function describeEvidence(entry: DeltaEvidence): string {
  if ("dependency" in entry) {
    return `${entry.dependency}: ${entry.before ?? "(baru)"} → ${entry.after}`;
  }
  if ("removed" in entry) {
    return `${entry.removed} dari ${entry.of} file teks hilang`;
  }
  if ("hook" in entry) {
    return `${entry.file} · ${entry.hook} — ${entry.match}`;
  }
  return `${entry.file}:${entry.line} — ${entry.match}`;
}
