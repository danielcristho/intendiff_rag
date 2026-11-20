import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { validAnnotator } from "@/lib/annotator";

const ALLOWED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-";
// Characters that matter in a path; random Unicode alone would almost never draw them.
const TRICKY = [".", "/", "\\", " ", "\0", "\n", ":", "~", "%", "é"];
const allowedChar = fc.constantFrom(...ALLOWED);
const outsider = fc.oneof(
  fc.constantFrom(...TRICKY),
  fc.string({ unit: "binary", minLength: 1, maxLength: 1 }).filter((c) => !ALLOWED.includes(c)),
);
const allowedName = fc.string({ unit: allowedChar, minLength: 1, maxLength: 32 });

describe("validAnnotator properties", () => {
  it("never accepts a name that could leave the decisions directory", () => {
    const anyName = fc.string({ unit: fc.oneof(allowedChar, outsider), maxLength: 40 });
    fc.assert(
      fc.property(anyName, (name) => {
        if (!validAnnotator(name)) return;
        expect(name).not.toMatch(/[/\\.\s\0]/);
        expect(name.length).toBeGreaterThanOrEqual(1);
        expect(name.length).toBeLessThanOrEqual(32);
      }),
      { numRuns: 2000 },
    );
  });

  it("accepts every name built only from letters, digits, _ and - up to 32 characters", () => {
    fc.assert(fc.property(allowedName, (name) => validAnnotator(name)));
  });

  it("rejects names longer than 32 characters even when every character is allowed", () => {
    const tooLong = fc.string({ unit: allowedChar, minLength: 33, maxLength: 64 });
    fc.assert(fc.property(tooLong, (name) => !validAnnotator(name)));
  });

  it("rejects a name once any other character is inserted", () => {
    fc.assert(
      fc.property(allowedName, outsider, fc.nat(), (name, bad, at) => {
        const i = at % (name.length + 1);
        return !validAnnotator(name.slice(0, i) + bad + name.slice(i));
      }),
    );
  });
});
