import { COLUMNS, groupByColumn, wasReturned } from "@/lib/cards";
import { cn } from "@/lib/utils";
import type { CardEntry, KbCard } from "@/types/api";

// CardBoard lays the cards out by workflow stage; a click opens one for editing.
export function CardBoard({
  cards,
  entries,
  onOpen,
}: {
  cards: KbCard[];
  entries: Record<string, CardEntry>;
  onOpen: (id: string) => void;
}) {
  const groups = groupByColumn(cards, entries);
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {COLUMNS.map(({ key, title }) => (
        <section key={key} className="min-w-0 rounded-xl bg-surface p-4 shadow-card">
          <h3 className="eyebrow">
            {title} <span className="font-mono text-ink-faint">({groups[key].length})</span>
          </h3>
          <div className="max-h-[70vh] space-y-1.5 overflow-y-auto">
            {groups[key].map((card) => {
              const entry = entries[card.id];
              const returned = wasReturned(entry);
              return (
                <button
                  key={card.id}
                  onClick={() => onOpen(card.id)}
                  className={cn(
                    "block w-full rounded border px-3 py-2 text-left transition-colors duration-100",
                    "hover:border-accent hover:bg-accent-soft",
                    returned ? "border-warn" : "border-hairline",
                  )}
                >
                  <div className="truncate font-mono text-xs text-ink">{card.name}</div>
                  <div className="mt-0.5 truncate font-mono text-[11px] text-ink-faint">
                    {card.delta.join(" · ") || "delta kosong"}
                  </div>
                  {(entry?.author || returned) && (
                    <div className="mt-1 text-[11px] text-ink-faint">
                      {entry?.author && <>✎ {entry.author}</>}
                      {entry?.reviewer && <> · ✓ {entry.reviewer}</>}
                      {returned && <span className="ml-1 font-semibold text-warn">dikembalikan</span>}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
