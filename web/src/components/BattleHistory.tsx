import { motion } from "framer-motion";
import { Sword, Trophy, Clock, Star } from "@phosphor-icons/react";
import { useApi } from "../hooks/useApi";
import { fetchPlayer } from "../api/client";
import { SkeletonRow } from "./Skeleton";
import type { Battle } from "../types";

const RESULT_STYLES = {
  victory: { bg: "bg-accent-muted", text: "text-accent", label: "WIN" },
  defeat: { bg: "bg-danger-muted", text: "text-danger", label: "LOSS" },
  draw: { bg: "bg-warn-muted", text: "text-warn", label: "DRAW" },
} as const;

export default function BattleHistory({ tag }: { tag: string }) {
  const { data: player, loading } = useApi(
    () => fetchPlayer(tag),
    [tag],
  );

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl rounded-2xl border border-line/40 bg-surface-1 p-6">
        <div className="mb-4 flex items-center gap-2">
          <Sword size={16} className="text-text-muted" />
          <h3 className="text-sm font-semibold text-text-primary">
            Recent Battles
          </h3>
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    );
  }

  const battles = player?.recent_battles ?? [];

  if (battles.length === 0) return null;

  return (
    <div className="mx-auto max-w-2xl rounded-2xl border border-line/40 bg-surface-1 p-6">
      <div className="mb-4 flex items-center gap-2">
        <Sword size={16} weight="fill" className="text-text-muted" />
        <h3 className="text-sm font-semibold text-text-primary">
          Recent Battles
        </h3>
        <span className="ml-auto font-mono text-xs text-text-muted">
          {battles.length} matches
        </span>
      </div>

      <div className="divide-y divide-line/30">
        {battles.map((battle, i) => (
          <BattleRow key={i} battle={battle} index={i} />
        ))}
      </div>
    </div>
  );
}

function BattleRow({ battle, index }: { battle: Battle; index: number }) {
  const style = RESULT_STYLES[battle.result] ?? RESULT_STYLES.draw;
  const time = new Date(battle.battle_time);
  const trophyStr =
    battle.trophy_change > 0
      ? `+${battle.trophy_change}`
      : String(battle.trophy_change);

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", stiffness: 120, damping: 20, delay: index * 0.04 }}
      className="flex items-center gap-4 py-3"
    >
      {/* Result badge */}
      <div
        className={`flex h-8 w-14 items-center justify-center rounded-lg font-mono text-[10px] font-bold ${style.bg} ${style.text}`}
      >
        {style.label}
      </div>

      {/* Brawler + mode */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">
          {battle.brawler_name}
          {battle.is_star_player && (
            <Star
              size={12}
              weight="fill"
              className="ml-1 inline text-warn"
            />
          )}
        </p>
        <p className="text-xs text-text-muted truncate">
          {battle.mode.replace(/([A-Z])/g, " $1").trim()}
          {battle.map_name && ` — ${battle.map_name}`}
        </p>
      </div>

      {/* Trophy change */}
      <span
        className={`font-mono text-sm font-bold ${
          battle.trophy_change > 0
            ? "text-accent"
            : battle.trophy_change < 0
              ? "text-danger"
              : "text-text-muted"
        }`}
      >
        <Trophy size={12} weight="fill" className="mr-1 inline" />
        {trophyStr}
      </span>

      {/* Duration */}
      {battle.duration != null && (
        <span className="hidden font-mono text-xs text-text-muted sm:flex sm:items-center sm:gap-1">
          <Clock size={12} />
          {Math.floor(battle.duration / 60)}:{String(battle.duration % 60).padStart(2, "0")}
        </span>
      )}

      {/* Time */}
      <span className="hidden font-mono text-[10px] text-text-muted lg:block">
        {time.toLocaleDateString(undefined, { month: "short", day: "numeric" })}
      </span>
    </motion.div>
  );
}
