import { describe, expect, it } from "vitest";
import {
  NO_FILTER,
  describeEvidence,
  intentSections,
  keep,
  summarize,
  type Filters,
} from "@/lib/audit";
import { validAnnotator } from "@/lib/annotator";
import type { Decisions, Pair } from "@/types/api";

const pair = (over: Partial<Pair>): Pair => ({ id: "x", name: "x", diff: "", ...over });
const f = (over: Partial<Filters>): Filters => ({ ...NO_FILTER, ...over });

describe("keep", () => {
  const decisions: Decisions = { a: { label: "benign" } };

  it("separates pairs that have not been reviewed", () => {
    expect(keep(pair({ id: "b" }), decisions, f({ status: "belum direview" }))).toBe(true);
    expect(keep(pair({ id: "a" }), decisions, f({ status: "belum direview" }))).toBe(false);
  });

  it("flags a disagreement only when pred and gold actually differ", () => {
    const g = f({ status: "beda dari gold" });
    expect(keep(pair({ pred: "MAL", label: "BEN" }), decisions, g)).toBe(true);
    expect(keep(pair({ pred: "BEN", label: "BEN" }), decisions, g)).toBe(false);
  });

  it("leaves the disagreement subset empty without a prediction", () => {
    const g = f({ status: "beda dari gold" });
    expect(keep(pair({ label: "BEN" }), decisions, g)).toBe(false);
    expect(keep(pair({}), decisions, g)).toBe(false);
  });

  it("filters by subset and by hard-negative category", () => {
    const hn3 = pair({ subset: "HN", category: 3 });
    expect(keep(hn3, decisions, f({ subset: "HN" }))).toBe(true);
    expect(keep(hn3, decisions, f({ subset: "MAL" }))).toBe(false);
    expect(keep(hn3, decisions, f({ category: 3 }))).toBe(true);
    expect(keep(hn3, decisions, f({ category: 4 }))).toBe(false);
    // A pair with no subset must not pass any subset filter.
    expect(keep(pair({}), decisions, f({ subset: "HN" }))).toBe(false);
  });

  it("combines filters instead of replacing one with another", () => {
    const hn1 = pair({ id: "b", subset: "HN", category: 1 });
    expect(keep(hn1, decisions, f({ subset: "HN", category: 1, status: "belum direview" }))).toBe(true);
    expect(keep(hn1, decisions, f({ subset: "HN", category: 2, status: "belum direview" }))).toBe(false);
  });

  it("passes everything when no filter is set", () => {
    expect(keep(pair({}), decisions, NO_FILTER)).toBe(true);
  });
});

describe("summarize", () => {
  it("counts only pairs that carry a decision", () => {
    const pairs = [pair({ id: "a" }), pair({ id: "b" }), pair({ id: "c" })];
    const decisions: Decisions = {
      a: { label: "benign" },
      b: { label: "malicious", error: "intent" },
      z: { label: "skip" }, // Orphan id: absent from pairs, must be ignored.
    };
    const s = summarize(pairs, decisions);
    expect(s.total).toBe(3);
    expect(s.reviewed).toBe(2);
    expect(s.byLabel).toEqual({ malicious: 1, benign: 1, skip: 0 });
    expect(s.byError).toEqual({ capability: 0, intent: 1, retrieval: 0 });
  });

  it("counts per-subset progress for Gate G1", () => {
    const pairs = [
      pair({ id: "m1", subset: "MAL" }),
      pair({ id: "m2", subset: "MAL" }),
      pair({ id: "h1", subset: "HN", category: 2 }),
      pair({ id: "t1", subset: "TYP" }),
    ];
    const s = summarize(pairs, { m1: { label: "malicious" }, h1: { label: "benign" } });
    expect(s.bySubset.MAL).toEqual({ total: 2, reviewed: 1 });
    expect(s.bySubset.HN).toEqual({ total: 1, reviewed: 1 });
    expect(s.bySubset.TYP).toEqual({ total: 1, reviewed: 0 });
  });
});

describe("validAnnotator", () => {
  it("rejects annotator names that escape the data directory", () => {
    // Must match valid_annotator in backend/src/store.rs exactly.
    for (const bad of ["", "../etc", "a/b", "a.b", "a b", "..", "x".repeat(33)]) {
      expect(validAnnotator(bad), bad).toBe(false);
    }
    for (const ok of ["A", "robby", "daniel-2", "anotator_B"]) {
      expect(validAnnotator(ok), ok).toBe(true);
    }
  });
});

describe("describeEvidence", () => {
  it("points a source match at its file and line", () => {
    expect(describeEvidence({ file: "scripts/setup.js", line: 2, match: "process.env" })).toBe(
      "scripts/setup.js:2 — process.env",
    );
  });

  it("names the lifecycle hook for an install script", () => {
    expect(describeEvidence({ file: "package.json", hook: "preinstall", match: "node s.js" })).toBe(
      "package.json · preinstall — node s.js",
    );
  });

  it("shows the old and new spec for a repointed dependency", () => {
    expect(
      describeEvidence({ dependency: "axios", before: "^1.0.0", after: "git+https://e.com/a.git" }),
    ).toBe("axios: ^1.0.0 → git+https://e.com/a.git");
  });

  it("marks a dependency that had no previous spec as new", () => {
    // A null `before` means the dependency was added, not repointed.
    expect(describeEvidence({ dependency: "x", before: null, after: "^1.0.0" })).toBe(
      "x: (baru) → ^1.0.0",
    );
  });

  it("reports counts for a large deletion", () => {
    expect(describeEvidence({ removed: 3, of: 4 })).toBe("3 dari 4 file teks hilang");
  });
});

describe("intentSections", () => {
  // Rendering the profile object itself as a React child blanked the audit page.
  it("turns a structured profile into labelled strings", () => {
    const sections = intentSections({
      description: "CLI parser",
      keywords: "not available",
      scripts: "test: mocha",
      readme: "# coa",
    });
    expect(sections.map(([label]) => label)).toEqual([
      "Description",
      "Keywords",
      "Scripts",
      "README excerpt",
    ]);
    expect(sections.every(([, text]) => typeof text === "string")).toBe(true);
  });

  it("still accepts the bare string of the sample pairs", () => {
    expect(intentSections("A formatter")).toEqual([["Description", "A formatter"]]);
  });
});
