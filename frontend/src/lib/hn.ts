import { CATEGORY_IDS } from "@/lib/audit";
import type { HnDocSource, HnSummary, HnVerification } from "@/types/api";

// Consts
export const QUOTA = 25;
export const DOC_SOURCES: HnDocSource[] = ["readme", "changelog", "commit", "issue"];

// acceptedPerCategory counts accepted candidates for each of the five §3.3 categories.
export function acceptedPerCategory(verifications: Record<string, HnVerification>): Record<number, number> {
  const counts: Record<number, number> = Object.fromEntries(CATEGORY_IDS.map((id) => [id, 0]));
  for (const entry of Object.values(verifications)) {
    if (entry.decision === "accept" && entry.category) counts[entry.category] += 1;
  }
  return counts;
}

// quotaMet reports whether every category has reached its quota, which ends the verification.
export function quotaMet(verifications: Record<string, HnVerification>): boolean {
  return Object.values(acceptedPerCategory(verifications)).every((count) => count >= QUOTA);
}

// nextUnverified returns the first candidate in queue order that has no decision yet.
export function nextUnverified(
  candidates: HnSummary[],
  verifications: Record<string, HnVerification>,
): HnSummary | undefined {
  return [...candidates]
    .sort((a, b) => a.queue_position - b.queue_position)
    .find((candidate) => !verifications[candidate.id]);
}

// npmUrl builds the registry page for a version; the link never comes from the sample itself.
export function npmUrl(name: string, version: string): string {
  return `https://www.npmjs.com/package/${name}/v/${encodeURIComponent(version)}`;
}
