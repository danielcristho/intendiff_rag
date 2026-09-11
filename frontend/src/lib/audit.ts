import type { Decisions, ErrorClass, Pair, Verdict } from "@/types/api";

export const FILTERS = ["semua", "belum direview", "beda dari gold"] as const;
export type Filter = (typeof FILTERS)[number];

export const VERDICTS: Verdict[] = ["malicious", "benign", "skip"];
export const ERRORS: ErrorClass[] = ["capability", "intent", "retrieval"];

export function keep(pair: Pair, decisions: Decisions, mode: Filter): boolean {
  if (mode === "belum direview") return !decisions[pair.id];
  // Tanpa `pred` sebuah pair belum bisa disebut beda dari gold — sebelum model
  // jalan (M5-6) subset ini memang harus kosong, bukan menyapu seluruh dataset.
  if (mode === "beda dari gold") return Boolean(pair.pred) && pair.pred !== pair.label;
  return true;
}

export interface Summary {
  total: number;
  reviewed: number;
  byLabel: Record<Verdict, number>;
  byError: Record<ErrorClass, number>;
  disagreements: number;
}

export function summarize(pairs: Pair[], decisions: Decisions): Summary {
  const byLabel = { malicious: 0, benign: 0, skip: 0 } as Record<Verdict, number>;
  const byError = { capability: 0, intent: 0, retrieval: 0 } as Record<ErrorClass, number>;
  let reviewed = 0;

  for (const pair of pairs) {
    const decision = decisions[pair.id];
    if (!decision) continue;
    reviewed += 1;
    if (decision.label) byLabel[decision.label] += 1;
    if (decision.error) byError[decision.error] += 1;
  }

  return {
    total: pairs.length,
    reviewed,
    byLabel,
    byError,
    disagreements: pairs.filter((p) => keep(p, decisions, "beda dari gold")).length,
  };
}
