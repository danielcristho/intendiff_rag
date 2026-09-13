// Verdict is the judgement an annotator or the model gives a pair.
export type Verdict = "malicious" | "benign" | "skip";
// ErrorClass is the EA4 taxonomy for why a model prediction went wrong.
export type ErrorClass = "capability" | "intent" | "retrieval";
// Subset is which part of the test set a pair belongs to.
export type Subset = "MAL" | "HN" | "TYP";

// Pair is one npm update under review; full schema in docs/experiments.md §3.
export interface Pair {
  id: string;
  name: string;
  before?: string;
  after?: string;
  diff: string;
  subset?: Subset;
  category?: number;
  campaign?: string;
  intent?: string;
  delta?: string[];
  truncated?: boolean;
  label?: string;
  pred?: string;
}

// Decision is one annotator's judgement on one pair.
export interface Decision {
  label?: Verdict;
  category?: number;
  error?: ErrorClass;
  note?: string;
  at?: string;
}

// Decisions maps a pair id to one annotator's decision on it.
export type Decisions = Record<string, Decision>;

// PairsResponse carries the pairs plus the filename they were read from.
export interface PairsResponse {
  source: string;
  pairs: Pair[];
}

// AnnotatorProgress is another annotator's decision count, never their labels.
export interface AnnotatorProgress {
  annotator: string;
  count: number;
}
