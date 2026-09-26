import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";
import { CapabilityDelta } from "@/components/audit/CapabilityDelta";
import { CardForm } from "@/components/cards/CardForm";
import { ReviewPanel } from "@/components/cards/ReviewPanel";
import { SampleBrowser } from "@/components/cards/SampleBrowser";
import { useAnnotator } from "@/components/AnnotatorGate";
import { useReviewCard, useWriteCard } from "@/hooks/useCards";
import { canReview, canWrite, columnOf, COLUMNS, errorMessage, wasReturned } from "@/lib/cards";
import type { CardEntry, CardText, KbCard } from "@/types/api";

// firstEvidenceFile opens the sample where the extractor saw the first signal.
function firstEvidenceFile(card: KbCard): string | undefined {
  for (const entries of Object.values(card.delta_evidence ?? {})) {
    for (const entry of entries) if ("file" in entry) return entry.file;
  }
  return undefined;
}

// CardWorkspace is one card: its metadata, the sample, the text, and the check.
export function CardWorkspace({ card, entry }: { card: KbCard; entry?: CardEntry }) {
  const { annotator } = useAnnotator();
  const [text, setText] = useState<CardText>({
    intent: entry?.intent ?? "",
    behavior_chain: entry?.behavior_chain ?? "",
    code_excerpt: entry?.code_excerpt ?? "",
    rationale: entry?.rationale ?? "",
  });
  const write = useWriteCard();
  const review = useReviewCard();
  const editable = canWrite(entry, annotator);
  const stage = COLUMNS.find(({ key }) => key === columnOf(entry))?.title;
  const failure = write.error ?? review.error;

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <div className="min-w-0 space-y-5">
        <Card>
          <div className="font-mono text-sm font-semibold text-ink">{card.id}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge value={card.label} />
            {stage && <Badge value={stage} />}
            {card.selected_for && <Badge value={`dipilih untuk ${card.selected_for}`} />}
            <Badge value={`kampanye ${card.campaign}`} />
          </div>
          <div className="mt-2 text-xs text-ink-faint">
            {entry?.author ? `ditulis ${entry.author}` : "belum ada penulis"}
            {entry?.reviewer && ` · dicek ${entry.reviewer}`}
            {entry?.at && ` · ${entry.at}`}
          </div>
          {wasReturned(entry) && (
            <p className="mt-3 rounded border border-warn bg-warn-soft p-2 text-sm text-warn">
              Dikembalikan {entry?.reviewer}: {entry?.note}
            </p>
          )}
          <CapabilityDelta item={card} />
        </Card>

        <CardForm
          text={text}
          editable={editable}
          busy={write.isPending}
          onChange={(patch) => setText((current) => ({ ...current, ...patch }))}
          onSave={(submit) => write.mutate({ id: card.id, text, submit })}
        />

        {entry && canReview(entry, annotator) && (
          <ReviewPanel
            entry={entry}
            busy={review.isPending}
            onReview={(approve, note) => review.mutate({ id: card.id, approve, note })}
          />
        )}
        {failure && <StateBlock tone="error">{errorMessage(failure)}</StateBlock>}
      </div>

      <SampleBrowser
        cardId={card.id}
        initialPath={firstEvidenceFile(card)}
        editable={editable}
        onUseExcerpt={(code_excerpt) => setText((current) => ({ ...current, code_excerpt }))}
      />
    </div>
  );
}
