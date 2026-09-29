import type {
  AnnotatorProgress,
  CardEntry,
  CardText,
  CardsResponse,
  Decision,
  Decisions,
  ModelResult,
  HnCandidate,
  HnQueueResponse,
  HnVerification,
  HnVerifyRequest,
  PairsResponse,
  SampleFile,
  Session,
  SampleText,
} from "@/types/api";
import { announceLogout, endsSession } from "@/lib/annotator";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // The session travels in an HttpOnly cookie that fetch sends for same-origin calls.
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (endsSession(path, response.status)) announceLogout();
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed (${response.status})`);
  }
  // 204 No Content has no body to parse.
  return (response.status === 204 ? undefined : await response.json()) as T;
}

const q = encodeURIComponent;

// api is the typed client for the Rust backend, proxied through /api in dev.
export const api = {
  login: (username: string, password: string) =>
    request<Session>("/api/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  session: () => request<Session>("/api/session"),
  logout: () => request<void>("/api/logout", { method: "POST" }),
  pairs: () => request<PairsResponse>("/api/pairs"),
  annotators: () => request<AnnotatorProgress[]>("/api/annotators"),
  results: (pairId: string) => request<ModelResult[]>(`/api/results?pair_id=${q(pairId)}`),
  decisions: () => request<Decisions>("/api/decisions"),
  saveDecision: (id: string, patch: Decision) =>
    request<Decision>(`/api/decisions?id=${q(id)}`, {
      method: "PUT",
      body: JSON.stringify(patch),
    }),
  cards: () => request<CardsResponse>("/api/cards"),
  writeCard: (id: string, text: CardText, submit: boolean) =>
    request<CardEntry>(`/api/cards?id=${q(id)}`, {
      method: "PUT",
      body: JSON.stringify({ ...text, submit }),
    }),
  reviewCard: (id: string, approve: boolean, note: string) =>
    request<CardEntry>(`/api/cards/review?id=${q(id)}`, {
      method: "PUT",
      body: JSON.stringify({ approve, note }),
    }),
  hnQueue: () => request<HnQueueResponse>("/api/hn/queue"),
  hnCandidate: (id: string) => request<HnCandidate>(`/api/hn/candidate?id=${q(id)}`),
  verifyHn: (id: string, body: HnVerifyRequest) =>
    request<HnVerification>(`/api/hn/verification?id=${q(id)}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  sampleFiles: (id: string) => request<SampleFile[]>(`/api/cards/files?id=${q(id)}`),
  sampleFile: (id: string, path: string) =>
    request<SampleText>(`/api/cards/file?id=${q(id)}&path=${q(path)}`),
};
