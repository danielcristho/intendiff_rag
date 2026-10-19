export function parseGoldEvidence(text: string, diff: string) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  const source = new Set(diff.split("\n"));
  return { lines, valid: lines.every((line) => source.has(line)) };
}
