import { describe, expect, it } from "vitest";
import { acceptedPerCategory, nextUnverified, npmUrl, quotaMet } from "@/lib/hn";
import type { HnSummary, HnVerification } from "@/types/api";

const candidate = (id: string, queue_position: number): HnSummary => ({
  id,
  name: id,
  before: "1",
  after: "2",
  source: "path-a",
  queue_position,
  delta: [],
  categories: [],
});

describe("acceptedPerCategory", () => {
  it("counts accepted candidates only, by the category the verifier chose", () => {
    const verifications: Record<string, HnVerification> = {
      a: { decision: "accept", category: 2 },
      b: { decision: "reject", reason: "undocumented" },
      c: { decision: "accept", category: 2 },
    };
    expect(acceptedPerCategory(verifications)).toEqual({ 1: 0, 2: 2, 3: 0, 4: 0, 5: 0 });
  });

  it("ends the verification only when all five categories are full", () => {
    const full = (category: number) =>
      Object.fromEntries(
        Array.from({ length: 25 }, (_, i) => [`${category}-${i}`, { decision: "accept", category }]),
      ) as Record<string, HnVerification>;
    const fourFull = { ...full(1), ...full(2), ...full(3), ...full(4) };
    expect(quotaMet(fourFull)).toBe(false);
    expect(quotaMet({ ...fourFull, ...full(5) })).toBe(true);
  });
});

describe("nextUnverified", () => {
  it("follows the queue position, not the order the list arrives in", () => {
    const queue = [candidate("late", 3), candidate("early", 1), candidate("middle", 2)];
    expect(nextUnverified(queue, {})?.id).toBe("early");
    expect(nextUnverified(queue, { early: { decision: "reject" } })?.id).toBe("middle");
  });
});

describe("npmUrl", () => {
  it("points at the registry page for the exact version, scoped names included", () => {
    expect(npmUrl("@elastic/ebt", "1.1.1")).toBe("https://www.npmjs.com/package/@elastic/ebt/v/1.1.1");
  });
});
