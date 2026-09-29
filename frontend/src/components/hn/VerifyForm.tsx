import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CATEGORY_IDS, HN_CATEGORIES } from "@/lib/audit";
import { DOC_SOURCES } from "@/lib/hn";
import type { HnDocSource, HnVerification, HnVerifyRequest } from "@/types/api";

const INPUT =
  "mt-1 w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent";

// VerifyForm records the §3.3 decision: category and documented purpose, or a reason to reject.
export function VerifyForm({
  current,
  busy,
  onSubmit,
}: {
  current?: HnVerification;
  busy: boolean;
  onSubmit: (body: HnVerifyRequest) => void;
}) {
  const [category, setCategory] = useState<number | undefined>(current?.category);
  const [source, setSource] = useState<HnDocSource | undefined>(current?.doc_source);
  const [reference, setReference] = useState(current?.doc_ref ?? "");
  const [reason, setReason] = useState(current?.reason ?? "");
  const canAccept = Boolean(category && source && reference.trim());

  return (
    <Card>
      <h3 className="eyebrow">Keputusan verifikasi (§3.3)</h3>
      {current && (
        <p className="mb-3 text-xs text-ink-faint">
          Tercatat: {current.decision} oleh {current.by} · {current.at}
        </p>
      )}
      <div className="text-xs font-semibold text-ink">Kategori menurut tujuan yang terdokumentasi</div>
      <div className="mt-1 space-y-1">
        {CATEGORY_IDS.map((id) => (
          <Button
            key={id}
            size="sm"
            variant={category === id ? "solid" : "default"}
            className="w-full justify-start"
            onClick={() => setCategory(id)}
          >
            {id}. {HN_CATEGORIES[id]}
          </Button>
        ))}
      </div>

      <div className="mt-4 text-xs font-semibold text-ink">Tujuan terdokumentasi di</div>
      <div className="mt-1 grid grid-cols-2 gap-1">
        {DOC_SOURCES.map((option) => (
          <Button key={option} size="sm" variant={source === option ? "solid" : "default"} onClick={() => setSource(option)}>
            {option}
          </Button>
        ))}
      </div>
      <label className="mt-3 block text-xs font-semibold text-ink">
        Rujukan: kutipan atau URL halaman dokumentasi
        <textarea rows={2} value={reference} onChange={(e) => setReference(e.target.value)} className={INPUT} />
      </label>
      <Button
        variant="solid"
        className="mt-3 w-full"
        disabled={busy || !canAccept}
        onClick={() => onSubmit({ accept: true, category, doc_source: source, doc_ref: reference })}
      >
        Terima sebagai HN
      </Button>

      <label className="mt-5 block text-xs font-semibold text-ink">
        Alasan menolak
        <input value={reason} onChange={(e) => setReason(e.target.value)} className={INPUT}
          placeholder="misal: tujuan tidak terdokumentasi" />
      </label>
      <Button
        variant="danger"
        className="mt-2 w-full"
        disabled={busy || !reason.trim()}
        onClick={() => onSubmit({ accept: false, reason })}
      >
        Tolak
      </Button>
    </Card>
  );
}
