import { describe, expect, it } from "vitest";
import { keep, summarize } from "@/lib/audit";
import type { Decisions, Pair } from "@/types/api";

const pair = (over: Partial<Pair>): Pair => ({ id: "x", name: "x", diff: "", ...over });

describe("keep", () => {
  const decisions: Decisions = { a: { label: "benign" } };

  it("memisahkan yang belum direview", () => {
    expect(keep(pair({ id: "b" }), decisions, "belum direview")).toBe(true);
    expect(keep(pair({ id: "a" }), decisions, "belum direview")).toBe(false);
  });

  it("hanya menandai beda ketika pred dan gold benar-benar berbeda", () => {
    expect(keep(pair({ pred: "MAL", label: "BEN" }), decisions, "beda dari gold")).toBe(true);
    expect(keep(pair({ pred: "BEN", label: "BEN" }), decisions, "beda dari gold")).toBe(false);
  });

  it("tanpa pred, subset disagreement kosong — bukan menyapu semua", () => {
    expect(keep(pair({ label: "BEN" }), decisions, "beda dari gold")).toBe(false);
    expect(keep(pair({}), decisions, "beda dari gold")).toBe(false);
  });

  it("mode semua meloloskan apa pun", () => {
    expect(keep(pair({}), decisions, "semua")).toBe(true);
  });
});

describe("summarize", () => {
  it("hanya menghitung pair yang punya keputusan", () => {
    const pairs = [pair({ id: "a" }), pair({ id: "b" }), pair({ id: "c" })];
    const decisions: Decisions = {
      a: { label: "benign" },
      b: { label: "malicious", error: "intent" },
      z: { label: "skip" }, // id yatim: tidak ada di pairs, harus diabaikan
    };
    const s = summarize(pairs, decisions);
    expect(s.total).toBe(3);
    expect(s.reviewed).toBe(2);
    expect(s.byLabel).toEqual({ malicious: 1, benign: 1, skip: 0 });
    expect(s.byError).toEqual({ capability: 0, intent: 1, retrieval: 0 });
  });
});
