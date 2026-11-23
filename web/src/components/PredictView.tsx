import { useState, useCallback } from "react";
import {
  ArrowUp,
  ArrowDown,
  MagnifyingGlass,
  Spinner,
  Trophy,
  Star,
  Sword,
  Lightning,
} from "@phosphor-icons/react";
import { motion, AnimatePresence } from "framer-motion";
import type { Prediction } from "../types";
import { fetchPrediction } from "../api/client";
import BattleHistory from "./BattleHistory";

const springIn = {
  type: "spring" as const,
  stiffness: 100,
  damping: 20,
};

export default function PredictView() {
  const [tag, setTag] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Prediction | null>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const clean = tag.trim();
      if (!clean) return;

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const data = await fetchPrediction(clean);
        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Prediction failed");
      } finally {
        setLoading(false);
      }
    },
    [tag],
  );

  return (
    <div className="space-y-8">
      {/* Search form */}
      <form onSubmit={handleSubmit} className="mx-auto max-w-xl">
        <label className="mb-2 block text-xs font-medium text-text-secondary">
          Player Tag
        </label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <MagnifyingGlass
              size={16}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted"
            />
            <input
              type="text"
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              placeholder="#8YVRRJQYY"
              className="w-full rounded-xl border border-line/60 bg-surface-1 py-3 pl-10 pr-4 font-mono text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/30 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !tag.trim()}
            className="flex items-center gap-2 rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-surface-0 transition-all hover:brightness-110 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Spinner size={16} className="animate-spin" />
            ) : (
              <Lightning size={16} weight="fill" />
            )}
            Predict
          </button>
        </div>
        {error && (
          <p className="mt-2 text-xs text-danger">{error}</p>
        )}
      </form>

      {/* Result */}
      <AnimatePresence mode="wait">
        {result && (
          <motion.div
            key={result.player_tag}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={springIn}
            className="space-y-6"
          >
            {/* Prediction card */}
            <div className="mx-auto max-w-2xl rounded-2xl border border-line/40 bg-surface-1 overflow-hidden">
              {/* Header bar */}
              <div
                className={`flex items-center justify-between px-6 py-4 ${
                  result.outcome === "gain"
                    ? "bg-accent-muted"
                    : "bg-danger-muted"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                      result.outcome === "gain"
                        ? "bg-accent/20"
                        : "bg-danger/20"
                    }`}
                  >
                    {result.outcome === "gain" ? (
                      <ArrowUp size={20} weight="bold" className="text-accent" />
                    ) : (
                      <ArrowDown size={20} weight="bold" className="text-danger" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text-primary">
                      {result.player_name}
                    </p>
                    <p className="font-mono text-xs text-text-muted">
                      {result.player_tag}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p
                    className={`text-2xl font-bold tracking-tight ${
                      result.outcome === "gain" ? "text-accent" : "text-danger"
                    }`}
                  >
                    {result.outcome === "gain" ? "+" : ""}
                    {result.predicted_trophy_change?.toFixed(0) ?? "?"}
                  </p>
                  <p className="text-xs text-text-muted">predicted over next 5 matches</p>
                </div>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-3 divide-x divide-line/40 border-b border-line/40">
                <StatCell
                  icon={Trophy}
                  label="Current"
                  value={result.current_trophies.toLocaleString()}
                />
                <StatCell
                  icon={Star}
                  label="Confidence"
                  value={`${(result.confidence * 100).toFixed(1)}%`}
                  accent
                />
                <StatCell
                  icon={Sword}
                  label="Prediction"
                  value={result.outcome === "gain" ? "Trophy Gain" : "Trophy Loss"}
                />
              </div>

              {/* Top features */}
              <div className="p-6">
                <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Top Contributing Factors
                </h3>
                <div className="space-y-3">
                  {result.top_features.map((feat, i) => (
                    <motion.div
                      key={feat.name}
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ ...springIn, delay: i * 0.06 }}
                      className="flex items-center gap-3"
                    >
                      <span className="w-5 font-mono text-xs text-text-muted">
                        {i + 1}
                      </span>
                      <div className="flex-1">
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-sm text-text-secondary">
                            {feat.name.replace(/_/g, " ")}
                          </span>
                          <span className="font-mono text-xs text-text-muted">
                            {feat.value.toFixed(2)}
                          </span>
                        </div>
                        <div className="h-1 overflow-hidden rounded-full bg-surface-2">
                          <motion.div
                            className="h-full rounded-full bg-accent"
                            initial={{ width: 0 }}
                            animate={{
                              width: `${Math.min(feat.importance * 100 * 5, 100)}%`,
                            }}
                            transition={{ ...springIn, delay: 0.2 + i * 0.06 }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>

            {/* Battle history */}
            <BattleHistory tag={result.player_tag} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      {!result && !loading && (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-1 border border-line/40">
            <Lightning size={28} className="text-text-muted" />
          </div>
          <p className="mb-1 text-sm font-medium text-text-secondary">
            Enter a player tag to get started
          </p>
          <p className="text-xs text-text-muted">
            We'll fetch the latest data and predict their trophy trend
          </p>
        </div>
      )}
    </div>
  );
}

function StatCell({
  icon: Icon,
  label,
  value,
  accent = false,
}: {
  icon: typeof Trophy;
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-1 py-4">
      <Icon size={14} className="text-text-muted" />
      <span
        className={`font-mono text-sm font-bold ${
          accent ? "text-accent" : "text-text-primary"
        }`}
      >
        {value}
      </span>
      <span className="text-[10px] text-text-muted">{label}</span>
    </div>
  );
}
