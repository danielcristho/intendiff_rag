import { NavLink, Outlet } from "react-router-dom";
import { Layers, LayoutDashboard, ScanSearch, UserRound } from "lucide-react";
import { useAnnotator } from "@/components/AnnotatorGate";

const NAV_LINKS = [
  { to: "/overview", label: "Overview", icon: LayoutDashboard },
  { to: "/audit", label: "Label Audit", icon: ScanSearch },
  { to: "/cards", label: "KB Cards", icon: Layers },
];

// AppLayout frames every page with the sidebar and the annotator header.
export function AppLayout() {
  const { annotator, clear } = useAnnotator();

  return (
    <div className="grid min-h-screen grid-cols-[240px_1fr] bg-canvas font-sans text-ink-soft">
      <aside className="sticky top-0 flex h-screen flex-col border-r border-hairline bg-surface px-4 py-5">
        <div className="space-y-7">
          <div className="px-2 pt-1 leading-tight">
            <div className="text-sm font-semibold text-ink">IntentDiff-RAG</div>
            <div className="font-mono text-xs text-ink-faint">npm update audit</div>
          </div>

          <nav className="space-y-0.5">
            <div className="eyebrow px-2">Research tooling</div>
            {NAV_LINKS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded px-3 py-2 text-sm transition-colors duration-100 ${
                    isActive
                      ? "bg-accent-soft font-semibold text-accent"
                      : "text-ink-soft hover:bg-canvas hover:text-ink"
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-hairline bg-surface px-8">
          <span className="text-xs text-ink-faint">
            Analisis statis — sampel tidak pernah dieksekusi
          </span>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-ink">
              <UserRound className="h-3.5 w-3.5 text-ink-faint" />
              <span className="font-mono">{annotator}</span>
            </span>
            <button
              onClick={clear}
              className="text-ink-faint underline-offset-2 hover:text-accent hover:underline"
            >
              ganti
            </button>
          </div>
        </header>
        <main className="min-w-0 flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
