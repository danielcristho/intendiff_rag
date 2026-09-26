import { useState, type MouseEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";
import { useSampleFile, useSampleFiles } from "@/hooks/useCards";
import { MAX_EXCERPT_LINES, excerpt, splitLines } from "@/lib/cards";
import { cn } from "@/lib/utils";

// SampleBrowser shows the sample's files as plain text and lifts a line range
// out verbatim, which is what §5.1 asks of code_excerpt.
export function SampleBrowser({
  cardId,
  initialPath,
  editable,
  onUseExcerpt,
}: {
  cardId: string;
  initialPath?: string;
  editable: boolean;
  onUseExcerpt: (text: string) => void;
}) {
  const [path, setPath] = useState(initialPath);
  const [range, setRange] = useState<[number, number] | null>(null);
  const files = useSampleFiles(cardId);
  const file = useSampleFile(cardId, path);

  const lines = file.data ? splitLines(file.data.text) : [];
  const [from, to] = range ? [Math.min(...range), Math.max(...range)] : [0, 0];
  const count = range ? to - from + 1 : 0;

  // A plain click starts a range; shift-click extends it.
  const pick = (line: number, event: MouseEvent) =>
    setRange((current) => (event.shiftKey && current ? [current[0], line] : [line, line]));

  const open = (next: string) => {
    setPath(next);
    setRange(null);
  };

  return (
    <Card className="min-w-0">
      <h3 className="eyebrow">Isi sampel</h3>
      <p className="mb-3 text-xs text-danger">
        Kode malicious — hanya ditampilkan sebagai teks, tidak pernah dijalankan.
      </p>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[200px_1fr]">
        <div className="max-h-[60vh] space-y-0.5 overflow-y-auto">
          {files.isError && <StateBlock tone="error">Gagal memuat daftar file.</StateBlock>}
          {files.data?.map((entry) => (
            <button
              key={entry.path}
              onClick={() => open(entry.path)}
              className={cn(
                "block w-full truncate rounded px-2 py-1 text-left font-mono text-xs",
                entry.path === path ? "bg-accent-soft text-accent" : "hover:bg-canvas",
              )}
              title={`${entry.path} · ${entry.size} byte`}
            >
              {entry.path}
            </button>
          ))}
        </div>

        <div className="min-w-0">
          {!path && <StateBlock>Pilih file di kiri.</StateBlock>}
          {file.isError && <StateBlock tone="error">Gagal memuat file.</StateBlock>}
          {file.data && (
            <>
              <pre className="max-h-[60vh] overflow-auto rounded border border-hairline bg-canvas font-mono text-[0.8em] leading-relaxed">
                {lines.map((text, i) => {
                  const line = i + 1;
                  const chosen = range && line >= from && line <= to;
                  return (
                    <div key={i} className={cn("flex", chosen && "bg-accent-soft")}>
                      <button
                        onClick={(event) => pick(line, event)}
                        className="w-12 shrink-0 select-none pr-2 text-right text-ink-faint hover:text-accent"
                      >
                        {line}
                      </button>
                      <span className="whitespace-pre pr-4">{text || " "}</span>
                    </div>
                  );
                })}
              </pre>
              {file.data.truncated && (
                <p className="mt-1 text-xs text-warn">File dipotong di 512 KiB.</p>
              )}
              <div className="mt-2 flex items-center gap-3 text-xs text-ink-faint">
                <span>Klik nomor baris, shift-klik untuk rentang.</span>
                {editable && (
                  <Button
                    size="sm"
                    disabled={!range || count > MAX_EXCERPT_LINES}
                    onClick={() => onUseExcerpt(excerpt(lines, from, to))}
                  >
                    {range
                      ? `Pakai baris ${from}–${to} (${count}) sebagai code_excerpt`
                      : "Pakai sebagai code_excerpt"}
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
