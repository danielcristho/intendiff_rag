import type { CardEntry, CardStage, KbCard } from "@/types/api";

export type Column = "empty" | CardStage;

export const COLUMNS: { key: Column; title: string }[] = [
  { key: "empty", title: "Kosong" },
  { key: "draft", title: "Draf" },
  { key: "submitted", title: "Menunggu cek" },
  { key: "approved", title: "Disetujui" },
];

export const MAX_EXCERPT_LINES = 15;

export function columnOf(entry: CardEntry | undefined): Column {
  return entry?.stage ?? "empty";
}

// groupByColumn places every card in the column of its current stage.
export function groupByColumn(
  cards: KbCard[],
  entries: Record<string, CardEntry>,
): Record<Column, KbCard[]> {
  const groups: Record<Column, KbCard[]> = { empty: [], draft: [], submitted: [], approved: [] };
  for (const card of cards) groups[columnOf(entries[card.id])].push(card);
  return groups;
}

// canWrite mirrors backend/src/modules/cards/service.rs so the UI never offers a refused edit.
export function canWrite(entry: CardEntry | undefined, annotator: string): boolean {
  if (entry?.stage === "approved") return false;
  return !entry?.author || entry.author === annotator;
}

export function canReview(entry: CardEntry | undefined, annotator: string): boolean {
  if (!entry?.author || entry.author === annotator) return false;
  return entry.stage === "submitted" || entry.stage === "approved";
}

// A returned card is a draft that already carries the reviewer's reason.
export function wasReturned(entry: CardEntry | undefined): boolean {
  return entry?.stage === "draft" && Boolean(entry.reviewer && entry.note);
}

// splitLines drops the line terminator, including the "\r" of CRLF samples.
export function splitLines(text: string): string[] {
  return text.split(/\r?\n/);
}

// excerpt returns lines first..last (1-based, inclusive, any order) verbatim.
export function excerpt(lines: string[], first: number, last: number): string {
  const [from, to] = first <= last ? [first, last] : [last, first];
  return lines.slice(from - 1, to).join("\n");
}

// errorMessage unwraps the backend's {"error": ...} body into plain text.
export function errorMessage(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error);
  try {
    return (JSON.parse(raw) as { error?: string }).error ?? raw;
  } catch {
    return raw;
  }
}
