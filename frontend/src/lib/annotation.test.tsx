import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { IntentView } from "@/components/audit/IntentView";
import { parseGoldEvidence } from "@/lib/goldEvidence";
import { DecisionPanel } from "@/components/audit/DecisionPanel";

describe("annotation inputs", () => {
  it("allows evidence and legitimate-purpose review without disclosing the source subset", () => {
    const html = renderToStaticMarkup(<DecisionPanel
      pair={{ id: "review-001", name: "package", diff: "+code", annotation_blinded: true }}
      entry={{}} onRecord={() => {}} />);
    expect(html).toContain("gold-evidence");
    expect(html).toContain("Process execution");
    expect(html).not.toContain("Error taxonomy");
  });
  it("renders the structured profile emitted by the real pipeline", () => {
    const html = renderToStaticMarkup(<IntentView intent={{
      description: "A tool", keywords: "npm", scripts: "postinstall: node setup.js",
      readme: "<script>sample text</script>",
    }} />);
    expect(html).toContain("postinstall: node setup.js");
    expect(html).toContain("&lt;script&gt;");
    expect(html).not.toContain("<script>");
  });

  it("preserves verbatim evidence and rejects paraphrases or whitespace edits", () => {
    const diff = '+  require("https");\n+process.env;';
    expect(parseGoldEvidence('+  require("https");\r\n', diff)).toEqual({
      lines: ['+  require("https");'], valid: true,
    });
    expect(parseGoldEvidence('+require("https");', diff).valid).toBe(false);
    expect(parseGoldEvidence("downloads a payload", diff).valid).toBe(false);
  });
});
