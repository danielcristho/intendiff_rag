import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  MALICIOUS: "bg-danger-soft text-danger",
  BENIGN: "bg-ok-soft text-ok",
  SKIP: "bg-warn-soft text-warn",
  CAPABILITY: "bg-accent-soft text-accent",
  INTENT: "bg-accent-soft text-accent",
  RETRIEVAL: "bg-accent-soft text-accent",
};

export function Badge({ value, className }: { value: string; className?: string }) {
  const key = value.split(" ").pop()?.toUpperCase() ?? "";
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold",
        tones[key] ?? "bg-canvas text-ink-soft",
        className,
      )}
    >
      {value}
    </span>
  );
}
