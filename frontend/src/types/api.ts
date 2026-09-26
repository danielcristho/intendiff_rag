export type Verdict = "malicious" | "benign" | "skip";
export type ErrorClass = "capability" | "intent" | "retrieval";
export type Subset = "MAL" | "HN" | "TYP";

export type DeltaEvidence =
  | { file: string; line: number; match: string }
  | { file: string; hook: string; match: string }
  | { dependency: string; before: string | null; after: string }
  | { removed: number; of: number };

// IntentProfile is pipeline/intent.py's output; "not available" marks an empty field.
export interface IntentProfile {
  description: string;
  keywords: string;
  scripts: string;
  readme: string;
}

export interface Pair {
  id: string;
  name: string;
  before?: string;
  after?: string;
  diff: string;
  subset?: Subset;
  category?: number;
  campaign?: string;
  intent?: IntentProfile | string;
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

export type CardStage = "draft" | "submitted" | "approved";

export interface CardText {
  intent: string;
  behavior_chain: string;
  code_excerpt: string;
  rationale: string;
}

// KbCard is one row of kb.skeleton.jsonl: chosen by pipeline/kb.py, text still to write.
export interface KbCard {
  id: string;
  name: string;
  label: string;
  campaign: string;
  source: string;
  delta: string[];
  selected_for?: string;
  root?: string;
  delta_evidence?: Record<string, DeltaEvidence[]>;
}

export interface CardEntry extends Partial<CardText> {
  stage?: CardStage;
  author?: string;
  reviewer?: string;
  note?: string;
  at?: string;
}

export interface CardsResponse {
  cards: KbCard[];
  entries: Record<string, CardEntry>;
}

export interface SampleFile {
  path: string;
  size: number;
}

export interface SampleText {
  path: string;
  text: string;
  truncated: boolean;
}
