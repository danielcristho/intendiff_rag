import { intentSections } from "@/lib/audit";
import type { Pair } from "@/types/api";

// IntentView shows the intent profile the way the prompt presents it.
export function IntentView({ intent }: { intent: Pair["intent"] }) {
  if (!intent) return <p className="text-sm italic text-ink-faint">belum ada intent profile</p>;
  return (
    <dl className="space-y-2 text-sm">
      {intentSections(intent).map(([label, text]) => (
        <div key={label}>
          <dt className="text-xs font-semibold text-ink">{label}</dt>
          <dd className="mt-0.5 max-h-48 overflow-y-auto whitespace-pre-wrap break-words text-ink-soft">
            {text}
          </dd>
        </div>
      ))}
    </dl>
  );
}
