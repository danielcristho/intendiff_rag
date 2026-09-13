// Verdict is the judgement an annotator or the model gives a pair.
export type Verdict = "malicious" | "benign" | "skip";
// ErrorClass is the EA4 taxonomy for why a model prediction went wrong.
export type ErrorClass = "capability" | "intent" | "retrieval";
// Subset is which part of the test set a pair belongs to.
export type Subset = "MAL" | "HN" | "TYP";

// DeltaEvidence is one reason a capability signal fired, from `capability.py --explain`.
//
// Four shapes, because the signals are not alike: a source match carries a
// line, an install hook carries the hook name, and the two change signals
// describe a manifest or a file count instead of a location.
export type DeltaEvidence =
  | { file: string; line: number; match: string }
  | { file: string; hook: string; match: string }
  | { dependency: string; before: string | null; after: string }
  | { removed: number; of: number };

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
  // Keyed by signal name; snake_case matches the pairs.jsonl schema.
  delta_evidence?: Record<string, DeltaEvidence[]>;
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

// RetrievedCard is one knowledge-base card as retrieval ranked and placed it.
export interface RetrievedCard {
  id: string;
  label: string;
  score: number;
  position: number;
}

// ModelResult is one recorded run, matching a results.jsonl row (§3).
export interface ModelResult {
  run_key: string;
  config: string;
  model: string;
  seed: number;
  temperature: number;
  cards: RetrievedCard[];
  verdict?: string | null;
  evidence?: string[] | null;
  reason?: string | null;
  json_valid?: boolean;
  finish_reason?: string | null;
  raw?: string;
  error?: string;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  latency_ms?: number;
}
