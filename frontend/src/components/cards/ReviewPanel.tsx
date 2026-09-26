import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { CardEntry } from "@/types/api";

// ReviewPanel is the second annotator's check against the sample's code.
export function ReviewPanel({
  entry,
  busy,
  onReview,
}: {
  entry: CardEntry;
  busy: boolean;
  onReview: (approve: boolean, note: string) => void;
}) {
  const [note, setNote] = useState("");
  return (
    <Card>
      <h3 className="eyebrow">Cek anotator kedua</h3>
      <p className="text-xs text-ink-faint">
        Bandingkan setiap field dengan kode di panel sampel. Mengembalikan card wajib disertai alasan.
      </p>
      <textarea
        rows={2}
        value={note}
        onChange={(event) => setNote(event.target.value)}
        placeholder="Alasan pengembalian, atau catatan persetujuan"
        className="mt-3 w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      />
      <div className="mt-3 flex gap-2">
        {entry.stage === "submitted" && (
          <Button variant="solid" disabled={busy} onClick={() => onReview(true, note)}>
            Setujui
          </Button>
        )}
        <Button variant="danger" disabled={busy || !note.trim()} onClick={() => onReview(false, note)}>
          Kembalikan ke penulis
        </Button>
      </div>
    </Card>
  );
}
