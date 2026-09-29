import { describe, expect, it } from "vitest";
import { endsSession } from "@/lib/annotator";

describe("endsSession", () => {
  it("logs out when an API call finds the session gone", () => {
    expect(endsSession("/api/pairs", 401)).toBe(true);
  });

  it("leaves the login form alone when the password or the session check fails", () => {
    // Treating the session check's 401 as a logout would make the gate re-ask forever.
    expect(endsSession("/api/login", 401)).toBe(false);
    expect(endsSession("/api/session", 401)).toBe(false);
  });

  it("ignores every other status", () => {
    expect(endsSession("/api/pairs", 403)).toBe(false);
    expect(endsSession("/api/pairs", 200)).toBe(false);
  });
});
