import type { Decision, Decisions, PairsResponse } from "@/types/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error((await res.text()) || `Request gagal (${res.status})`);
  return (await res.json()) as T;
}

export const api = {
  pairs: () => request<PairsResponse>("/api/pairs"),
  decisions: () => request<Decisions>("/api/decisions"),
  saveDecision: (id: string, patch: Decision) =>
    request<Decision>(`/api/decisions?id=${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(patch),
    }),
};
