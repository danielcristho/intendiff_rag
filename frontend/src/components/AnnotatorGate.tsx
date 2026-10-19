import { createContext, useContext, useState, type FormEvent, type ReactNode } from "react";
import { getAnnotator, setAnnotator, validAnnotator } from "@/lib/annotator";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const Ctx = createContext<{ annotator: string; clear: () => void } | null>(null);

// useAnnotator returns the signed-in annotator and a way to sign out.
export function useAnnotator() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAnnotator used outside AnnotatorGate");
  return value;
}

// AnnotatorGate asks who is labelling before letting any page render.
export function AnnotatorGate({ children }: { children: ReactNode }) {
  const [annotator, setCurrent] = useState(getAnnotator);
  const [draft, setDraft] = useState("");

  if (annotator) {
    return (
      <Ctx.Provider value={{ annotator, clear: () => setCurrent("") }}>{children}</Ctx.Provider>
    );
  }

  const ok = validAnnotator(draft);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!ok) return;
    setAnnotator(draft);
    setCurrent(draft);
  };

  return (
    <div className="grid min-h-screen place-items-center bg-canvas p-8 font-sans text-ink-soft">
      <Card className="w-full max-w-md">
        <h1 className="text-lg">Siapa yang melabeli?</h1>
        <p className="mt-1 text-sm">
          Keputusanmu disimpan terpisah dari anotator lain supaya Cohen&apos;s κ bisa dihitung.
        </p>
        <form onSubmit={submit} className="mt-4 space-y-3">
          <input
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="misal: robby"
            className="w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          />
          <p className="text-xs text-ink-faint">
            Huruf, angka, <code className="font-mono">_</code> atau <code className="font-mono">-</code>, maksimal 32 karakter.
          </p>
          <Button type="submit" variant="solid" disabled={!ok} className="w-full">
            Mulai melabeli
          </Button>
        </form>
      </Card>
    </div>
  );
}
