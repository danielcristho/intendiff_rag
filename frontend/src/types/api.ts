export type Verdict = "malicious" | "benign" | "skip";
export type ErrorClass = "capability" | "intent" | "retrieval";
export type Subset = "MAL" | "HN" | "TYP";

export type DeltaEvidence =
  | { file: string; line: number; match: string }
  | { file: string; hook: string; match: string }
  | { dependency: string; before: string | null; after: string }
  | { removed: number; of: number };

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
  delta_evidence?: Record<string, DeltaEvidence[]>;
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

export type Decisions = Record<string, Decision>;

export interface PairsResponse {
  source: string;
  pairs: Pair[];
}

export interface AnnotatorProgress {
  annotator: string;
  count: number;
}

export interface RetrievedCard {
  id: string;
  label: string;
  score: number;
  position: number;
}

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
