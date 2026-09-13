export type Verdict = "malicious" | "benign" | "skip";
export type ErrorClass = "capability" | "intent" | "retrieval";
export type Subset = "MAL" | "HN" | "TYP";

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
