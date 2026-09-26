import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { StateBlock } from "@/components/ui/state-block";
import { CardBoard } from "@/components/cards/CardBoard";
import { CardWorkspace } from "@/components/cards/CardWorkspace";
import { useCards } from "@/hooks/useCards";
import { groupByColumn } from "@/lib/cards";

// CardsPage moves KB cards from selection to kb.jsonl: written by one
// annotator, checked by another, then promoted from the command line.
export function CardsPage() {
  const [params, setParams] = useSearchParams();
  const cardsQuery = useCards();
  const openId = params.get("card");

  if (cardsQuery.isLoading) return <StateBlock>Memuat card…</StateBlock>;
  if (cardsQuery.isError)
    return <StateBlock tone="error">Gagal memuat: {String(cardsQuery.error)}</StateBlock>;

  const { cards, entries } = cardsQuery.data!;
  if (!cards.length)
    return (
      <StateBlock>
        Belum ada <code className="font-mono">data/kb.skeleton.jsonl</code> — jalankan{" "}
        <code className="font-mono">python pipeline/kb.py</code> dulu.
      </StateBlock>
    );

  const card = cards.find(({ id }) => id === openId);
  if (card) {
    return (
      <div className="space-y-5">
        <Button size="sm" onClick={() => setParams({})}>
          ← Kembali ke papan
        </Button>
        {/* Keyed so the form state resets when another card opens. */}
        <CardWorkspace key={card.id} card={card} entry={entries[card.id]} />
      </div>
    );
  }

  const approved = groupByColumn(cards, entries).approved.length;
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="text-lg text-ink">
          KB cards <span className="font-mono text-sm text-ink-faint">{approved}/{cards.length} disetujui</span>
        </h1>
        <p className="text-xs text-ink-faint">
          Setelah semua disetujui:{" "}
          <code className="rounded bg-surface px-1.5 py-0.5 font-mono">python pipeline/promote.py</code>{" "}
          menulis <code className="font-mono">data/kb.jsonl</code>.
        </p>
      </div>
      <CardBoard cards={cards} entries={entries} onOpen={(id) => setParams({ card: id })} />
    </div>
  );
}
