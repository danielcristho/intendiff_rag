export type Verdict = "malicious" | "benign" | "skip";
export type ErrorClass = "capability" | "intent" | "retrieval";

/**
 * Satu pasangan update. Hanya id/name/diff yang wajib — `intent`, `delta`,
 * `label`, dan `pred` menyusul seiring pipeline jalan, jadi UI ini dipakai
 * untuk label audit (M1-2) sekarang dan error analysis (M7-8) nanti tanpa
 * mengunci schema verdict JSON yang belum stabil.
 */
export interface Pair {
  id: string;
  name: string;
  before?: string;
  after?: string;
  diff: string;
  intent?: string;
  delta?: string[];
  label?: string;
  pred?: string;
}

export interface Decision {
  label?: Verdict;
  error?: ErrorClass;
  note?: string;
  at?: string;
}

export type Decisions = Record<string, Decision>;

export interface PairsResponse {
  source: string;
  pairs: Pair[];
}
