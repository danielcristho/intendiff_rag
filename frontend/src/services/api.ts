import type {
  AnnotatorProgress,
  Decision,
  Decisions,
  ModelResult,
  PairsResponse,
} from "@/types/api";

// request issues a JSON call and turns any non-2xx response into an error.
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
};
