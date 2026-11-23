import { useState } from "react";
import {
  Brain,
  ChartLineUp,
  Users,
} from "@phosphor-icons/react";
import Overview from "./components/Overview";
import PredictView from "./components/PredictView";
import PlayersView from "./components/PlayersView";
import type { View } from "./types";

const NAV_ITEMS: { id: View; label: string; icon: typeof Brain }[] = [
  { id: "overview", label: "Overview", icon: ChartLineUp },
  { id: "predict", label: "Predict", icon: Brain },
  { id: "players", label: "Players", icon: Users },
];

export default function App() {
  const [view, setView] = useState<View>("overview");

  return (
    <div className="min-h-[100dvh] bg-surface-0 font-sans">
      {/* Header */}
      <header className="border-b border-line/50">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-muted">
                <Brain size={20} weight="fill" className="text-accent" />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight text-text-primary">
                  Brawl Predictor
                </h1>
                <p className="text-xs text-text-muted">
                  ML-powered performance predictions
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex items-center gap-1 rounded-xl bg-surface-1 p-1">
              {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setView(id)}
                  className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all active:scale-[0.98] ${
                    view === id
                      ? "bg-surface-2 text-text-primary"
                      : "text-text-muted hover:text-text-secondary"
                  }`}
                >
                  <Icon size={16} weight={view === id ? "fill" : "regular"} />
                  <span className="hidden sm:inline">{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-6xl px-6 py-8">
        {view === "overview" && <Overview />}
        {view === "predict" && <PredictView />}
        {view === "players" && <PlayersView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-line/50 py-8 text-center font-mono text-xs text-text-muted">
        Data from the{" "}
        <a
          href="https://developer.brawlstars.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-text-secondary transition-colors hover:text-accent"
        >
          Brawl Stars API
        </a>
        {" "}&mdash; not affiliated with Supercell.
      </footer>
    </div>
  );
}
