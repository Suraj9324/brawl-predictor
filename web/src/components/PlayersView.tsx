import { useState, useCallback } from "react";
import {
  Plus,
  Trash,
  Trophy,
  ArrowsClockwise,
  Spinner,
  UserCirclePlus,
} from "@phosphor-icons/react";
import { motion, AnimatePresence } from "framer-motion";
import { useApi } from "../hooks/useApi";
import {
  addPlayer,
  fetchPlayers,
  removePlayer,
} from "../api/client";
import { SkeletonRow } from "./Skeleton";
import type { Player } from "../types";

const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { type: "spring" as const, stiffness: 120, damping: 20 },
};

export default function PlayersView() {
  const { data: players, loading, refetch } = useApi(fetchPlayers, []);
  const [showAdd, setShowAdd] = useState(false);
  const [newTag, setNewTag] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);

  const handleAdd = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const clean = newTag.trim();
      if (!clean) return;

      setAdding(true);
      setAddError(null);
      try {
        await addPlayer(clean);
        setNewTag("");
        setShowAdd(false);
        refetch();
      } catch (err) {
        setAddError(err instanceof Error ? err.message : "Failed to add player");
      } finally {
        setAdding(false);
      }
    },
    [newTag, refetch],
  );

  const handleRemove = useCallback(
    async (tag: string) => {
      setRemoving(tag);
      try {
        await removePlayer(tag);
        refetch();
      } catch {
        // silently fail
      } finally {
        setRemoving(null);
      }
    },
    [refetch],
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-text-primary">
            Tracked Players
          </h2>
          <p className="text-xs text-text-muted">
            {players?.length ?? 0} players being monitored
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refetch}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-line/60 bg-surface-1 text-text-muted transition-colors hover:text-text-secondary active:scale-[0.96]"
          >
            <ArrowsClockwise size={16} />
          </button>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-surface-0 transition-all hover:brightness-110 active:scale-[0.98]"
          >
            <Plus size={16} weight="bold" />
            Add Player
          </button>
        </div>
      </div>

      {/* Add form */}
      <AnimatePresence>
        {showAdd && (
          <motion.form
            {...fadeUp}
            onSubmit={handleAdd}
            className="rounded-2xl border border-line/40 bg-surface-1 p-5"
          >
            <label className="mb-2 block text-xs font-medium text-text-secondary">
              Player Tag
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                placeholder="#8YVRRJQYY"
                autoFocus
                className="flex-1 rounded-xl border border-line/60 bg-surface-2 py-2.5 px-4 font-mono text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/30 transition-colors"
              />
              <button
                type="submit"
                disabled={adding || !newTag.trim()}
                className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-surface-0 transition-all hover:brightness-110 active:scale-[0.98] disabled:opacity-40"
              >
                {adding ? (
                  <Spinner size={16} className="animate-spin" />
                ) : (
                  <UserCirclePlus size={16} weight="fill" />
                )}
                Add
              </button>
            </div>
            {addError && (
              <p className="mt-2 text-xs text-danger">{addError}</p>
            )}
          </motion.form>
        )}
      </AnimatePresence>

      {/* Player list */}
      <div className="rounded-2xl border border-line/40 bg-surface-1">
        {loading ? (
          <div className="p-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </div>
        ) : players && players.length > 0 ? (
          <div className="divide-y divide-line/30">
            {players.map((player, i) => (
              <PlayerRow
                key={player.tag}
                player={player}
                index={i}
                removing={removing === player.tag}
                onRemove={handleRemove}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-2 border border-line/40">
              <UserCirclePlus size={24} className="text-text-muted" />
            </div>
            <p className="mb-1 text-sm font-medium text-text-secondary">
              No players tracked yet
            </p>
            <p className="text-xs text-text-muted">
              Add a player tag to start collecting data
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function PlayerRow({
  player,
  index,
  removing,
  onRemove,
}: {
  player: Player;
  index: number;
  removing: boolean;
  onRemove: (tag: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", stiffness: 120, damping: 20, delay: index * 0.04 }}
      className="group flex items-center gap-4 px-6 py-4"
    >
      {/* Rank-style number */}
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-2 font-mono text-xs font-bold text-text-muted">
        {index + 1}
      </span>

      {/* Player info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-text-primary truncate">
          {player.name}
        </p>
        <p className="font-mono text-xs text-text-muted truncate">
          {player.tag}
          {player.club_name && (
            <span className="ml-2 text-text-muted/60">
              {player.club_name}
            </span>
          )}
        </p>
      </div>

      {/* Trophies */}
      <div className="flex items-center gap-1.5">
        <Trophy size={14} weight="fill" className="text-warn" />
        <span className="font-mono text-sm font-bold text-text-primary">
          {player.trophies.toLocaleString()}
        </span>
      </div>

      {/* Highest */}
      <div className="hidden items-center gap-1.5 sm:flex">
        <Trophy size={12} className="text-text-muted" />
        <span className="font-mono text-xs text-text-muted">
          {player.highest_trophies.toLocaleString()}
        </span>
      </div>

      {/* Level */}
      <span className="hidden font-mono text-xs text-text-muted lg:block">
        Lv. {player.experience_level}
      </span>

      {/* Last synced */}
      <span className="hidden font-mono text-[10px] text-text-muted xl:block">
        {player.last_synced_at
          ? new Date(player.last_synced_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })
          : "never"}
      </span>

      {/* Delete */}
      <button
        onClick={() => onRemove(player.tag)}
        disabled={removing}
        className="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted opacity-0 transition-all hover:bg-danger-muted hover:text-danger group-hover:opacity-100 disabled:opacity-50"
      >
        {removing ? (
          <Spinner size={14} className="animate-spin" />
        ) : (
          <Trash size={14} />
        )}
      </button>
    </motion.div>
  );
}
