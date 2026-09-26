import type {
  AnnotatorProgress,
  CardEntry,
  CardText,
  CardsResponse,
  Decision,
  Decisions,
  ModelResult,
  PairsResponse,
  SampleFile,
  SampleText,
} from "@/types/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

const q = encodeURIComponent;

// api is the typed client for the Rust backend, proxied through /api in dev.
export const api = {
  pairs: () => request<PairsResponse>("/api/pairs"),
  annotators: () => request<AnnotatorProgress[]>("/api/annotators"),
  results: (pairId: string) => request<ModelResult[]>(`/api/results?pair_id=${q(pairId)}`),
  decisions: (annotator: string) => request<Decisions>(`/api/decisions?annotator=${q(annotator)}`),
  saveDecision: (annotator: string, id: string, patch: Decision) =>
    request<Decision>(`/api/decisions?id=${q(id)}&annotator=${q(annotator)}`, {
      method: "PUT",
      body: JSON.stringify(patch),
    }),
  cards: () => request<CardsResponse>("/api/cards"),
  writeCard: (annotator: string, id: string, text: CardText, submit: boolean) =>
    request<CardEntry>(`/api/cards?id=${q(id)}&annotator=${q(annotator)}`, {
      method: "PUT",
      body: JSON.stringify({ ...text, submit }),
    }),
  reviewCard: (annotator: string, id: string, approve: boolean, note: string) =>
    request<CardEntry>(`/api/cards/review?id=${q(id)}&annotator=${q(annotator)}`, {
      method: "PUT",
      body: JSON.stringify({ approve, note }),
    }),
  sampleFiles: (id: string) => request<SampleFile[]>(`/api/cards/files?id=${q(id)}`),
  sampleFile: (id: string, path: string) =>
    request<SampleText>(`/api/cards/file?id=${q(id)}&path=${q(path)}`),
};
