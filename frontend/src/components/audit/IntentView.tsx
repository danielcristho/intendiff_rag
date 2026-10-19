import type { Pair } from "@/types/api";

export function IntentView({ intent }: { intent: Pair["intent"] }) {
  if (!intent) return <p className="italic text-ink-faint">No intent profile available</p>;
  if (typeof intent === "string") return <p className="whitespace-pre-wrap text-sm">{intent}</p>;
  return (
    <dl className="space-y-3 text-sm">
      {(["description", "keywords", "scripts", "readme"] as const).map((field) => (
        <div key={field}>
          <dt className="font-semibold capitalize">{field}</dt>
          <dd className="max-h-60 overflow-auto whitespace-pre-wrap break-words">{intent[field]}</dd>
        </div>
      ))}
    </dl>
  );
}
