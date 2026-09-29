import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LOGGED_OUT, validAnnotator } from "@/lib/annotator";
import { errorMessage } from "@/lib/cards";
import { api } from "@/services/api";
import type { Session } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StateBlock } from "@/components/ui/state-block";

const Ctx = createContext<{ annotator: string; clear: () => Promise<void> } | null>(null);
const SESSION_KEY = ["session"] as const;

// useAnnotator returns the signed-in annotator and a way to sign out.
export function useAnnotator() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAnnotator used outside AnnotatorGate");
  return value;
}

const INPUT =
  "w-full rounded border border-line bg-surface p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent";

// AnnotatorGate asks the backend who holds the session cookie and shows the login form if no one does.
export function AnnotatorGate({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const session = useQuery<Session | null>({
    queryKey: SESSION_KEY,
    queryFn: api.session,
    retry: false,
  });

  // endSession drops the previous annotator's cached data along with the session.
  const endSession = useCallback(() => {
    queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== SESSION_KEY[0] });
    queryClient.setQueryData(SESSION_KEY, null);
  }, [queryClient]);

  useEffect(() => {
    window.addEventListener(LOGGED_OUT, endSession);
    return () => window.removeEventListener(LOGGED_OUT, endSession);
  }, [endSession]);

  if (session.isPending) return <StateBlock>Memeriksa sesi…</StateBlock>;
  if (!session.data) {
    return <LoginForm onLogin={(next) => queryClient.setQueryData(SESSION_KEY, next)} />;
  }

  const clear = () => api.logout().finally(endSession);
  return (
    <Ctx.Provider value={{ annotator: session.data.annotator, clear }}>{children}</Ctx.Provider>
  );
}

function LoginForm({ onLogin }: { onLogin: (session: Session) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const ok = validAnnotator(username) && password.length > 0;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!ok) return;
    setBusy(true);
    setError("");
    try {
      onLogin(await api.login(username, password));
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen place-items-center bg-canvas p-8 font-sans text-ink-soft">
      <Card className="w-full max-w-md">
        <h1 className="text-lg">Masuk sebagai anotator</h1>
        <p className="mt-1 text-sm">
          Keputusanmu disimpan terpisah dari anotator lain supaya Cohen&apos;s κ bisa dihitung.
        </p>
        <form onSubmit={submit} className="mt-4 space-y-3">
          <input
            autoFocus
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="username"
            className={INPUT}
          />
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
            className={INPUT}
          />
          {error && (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          )}
          <p className="text-xs text-ink-faint">
            Akun dibuat di server:{" "}
            <code className="font-mono">intentdiff-backend user-add &lt;username&gt;</code>
          </p>
          <Button type="submit" variant="solid" disabled={!ok || busy} className="w-full">
            {busy ? "Memeriksa…" : "Masuk"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
