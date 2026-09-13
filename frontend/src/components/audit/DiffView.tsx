import { cn } from "@/lib/utils";

// DiffView renders a smart-diff line by line, tinted by its change marker.
export function DiffView({ diff }: { diff: string }) {
  const lines = diff.split("\n");
  return (
    <pre className="overflow-x-auto rounded border border-hairline bg-canvas p-0 font-mono text-[0.85em] leading-relaxed">
      {lines.map((line, i) => {
        const added = line.startsWith("+") && !line.startsWith("+++");
        const removed = line.startsWith("-") && !line.startsWith("---");
        const meta = line.startsWith("@@") || line.startsWith("+++") || line.startsWith("---");
        return (
          <div
            key={i}
            className={cn(
              "whitespace-pre px-4 py-0.5",
              added && "bg-ok-soft text-ok",
              removed && "bg-danger-soft text-danger",
              meta && "text-ink-faint",
            )}
          >
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}
