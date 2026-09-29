import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { GoldEvidence } from "@/components/audit/GoldEvidence";
import { CATEGORY_IDS, ERRORS, HN_CATEGORIES, VERDICTS } from "@/lib/audit";
import type { Decision, ErrorClass, Pair, Verdict } from "@/types/api";

// DecisionPanel records the annotator's verdict, category, error class and note.
export function DecisionPanel({
  pair,
  entry,
  onRecord,
}: {
  pair: Pair;
  entry: Decision;
  onRecord: (patch: Decision) => void;
}) {
  return (
    <Card>
      <h3 className="eyebrow">
        Verdict <span className="font-mono normal-case text-ink-faint">(m / b / s)</span>
      </h3>
      <div className="grid grid-cols-3 gap-2">
        {VERDICTS.map((verdict: Verdict) => (
          <Button
            key={verdict}
            size="sm"
            variant={entry.label === verdict ? "solid" : "default"}
            onClick={() => onRecord({ label: verdict })}
          >
            {verdict}
          </Button>
        ))}
      </div>

      {pair.subset === "HN" && (
        <>
          <h3 className="eyebrow mt-5">Kategori hard negative</h3>
          <div className="space-y-1.5">
            {CATEGORY_IDS.map((category) => (
              <Button
                key={category}
                size="sm"
                variant={entry.category === category ? "solid" : "default"}
                className="w-full justify-start"
                onClick={() => onRecord({ category })}
              >
                {category}. {HN_CATEGORIES[category]}
              </Button>
            ))}
          </div>
        </>
      )}

      {pair.pred && (
        <>
          <h3 className="eyebrow mt-5">Error taxonomy</h3>
          <div className="grid grid-cols-3 gap-2">
            {ERRORS.map((errorClass: ErrorClass) => (
              <Button
                key={errorClass}
                size="sm"
                variant={entry.error === errorClass ? "solid" : "default"}
                onClick={() => onRecord({ error: errorClass })}
              >
                {errorClass}
              </Button>
            ))}
          </div>
        </>
      )}

      {pair.subset === "MAL" && <GoldEvidence key={pair.id} pair={pair} entry={entry} onRecord={onRecord} />}

      <textarea
        // Remounting per pair keeps the uncontrolled value from leaking across pairs.
        key={pair.id}
        className="mt-4 w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        rows={3}
        placeholder="Catatan — alasan ketidaksepakatan ditulis di sini (§8)"
        defaultValue={entry.note ?? ""}
        onBlur={(event) => onRecord({ note: event.target.value })}
      />
    </Card>
  );
}
