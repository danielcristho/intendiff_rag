import { describe, expect, it } from "vitest";
import { canReview, canWrite, errorMessage, excerpt, groupByColumn, splitLines, wasReturned } from "@/lib/cards";
import type { KbCard } from "@/types/api";

const card = (id: string): KbCard => ({
  id,
  name: id,
  label: "malicious",
  campaign: id,
  source: "datadog",
  delta: [],
});

describe("groupByColumn", () => {
  it("puts a card with no entry in the empty column and never loses one", () => {
    const groups = groupByColumn([card("a"), card("b"), card("c")], {
      b: { stage: "submitted", author: "A" },
      c: { stage: "approved", author: "A", reviewer: "B" },
    });
    expect(groups.empty.map((c) => c.id)).toEqual(["a"]);
    expect(groups.submitted.map((c) => c.id)).toEqual(["b"]);
    expect(groups.approved.map((c) => c.id)).toEqual(["c"]);
    expect(Object.values(groups).flat()).toHaveLength(3);
  });
});

describe("permissions", () => {
  it("lets anyone claim an empty card but only its author edit it afterwards", () => {
    expect(canWrite(undefined, "B")).toBe(true);
    expect(canWrite({ stage: "draft", author: "A" }, "A")).toBe(true);
    expect(canWrite({ stage: "draft", author: "A" }, "B")).toBe(false);
  });

  it("freezes an approved card for its author", () => {
    expect(canWrite({ stage: "approved", author: "A" }, "A")).toBe(false);
  });

  it("never offers the author a review of their own card", () => {
    expect(canReview({ stage: "submitted", author: "A" }, "A")).toBe(false);
    expect(canReview({ stage: "submitted", author: "A" }, "B")).toBe(true);
    expect(canReview({ stage: "draft", author: "A" }, "B")).toBe(false);
    expect(canReview(undefined, "B")).toBe(false);
  });

  it("tells a returned draft apart from one never reviewed", () => {
    expect(wasReturned({ stage: "draft", author: "A", reviewer: "B", note: "vague" })).toBe(true);
    expect(wasReturned({ stage: "draft", author: "A" })).toBe(false);
  });
});

describe("excerpt", () => {
  it("copies the chosen lines verbatim, without CRLF residue", () => {
    const lines = splitLines("a\r\n  b();\r\nc\r\n");
    expect(excerpt(lines, 2, 3)).toBe("  b();\nc");
    expect(excerpt(lines, 3, 2)).toBe("  b();\nc");
  });
});

describe("errorMessage", () => {
  it("shows the backend's reason rather than raw JSON", () => {
    expect(errorMessage(new Error('{"error":"alasan pengembalian wajib diisi"}'))).toBe(
      "alasan pengembalian wajib diisi",
    );
    expect(errorMessage(new Error("Request failed (502)"))).toBe("Request failed (502)");
  });
});
