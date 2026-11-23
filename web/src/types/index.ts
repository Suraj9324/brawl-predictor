export interface Player {
  id: number;
  tag: string;
  name: string;
  trophies: number;
  highest_trophies: number;
  experience_level: number;
  club_name: string | null;
  is_tracked: boolean;
  last_synced_at: string | null;
  created_at: string;
}

export interface PlayerDetail extends Player {
  snapshots: Snapshot[];
  recent_battles: Battle[];
  brawler_count: number;
}

export interface Snapshot {
  trophies: number;
  highest_trophies: number;
  brawlers_count: number;
  avg_brawler_power: number;
  timestamp: string;
}

export interface Battle {
  battle_time: string;
  mode: string;
  map_name: string | null;
  result: "victory" | "defeat" | "draw";
  trophy_change: number;
  brawler_name: string;
  brawler_power: number;
  is_star_player: boolean;
  duration: number | null;
}

export interface TopFeature {
  name: string;
  value: number;
  importance: number;
}

export interface Prediction {
  player_tag: string;
  player_name: string;
  outcome: "gain" | "loss";
  confidence: number;
  predicted_trophy_change: number | null;
  top_features: TopFeature[];
  current_trophies: number;
}

export interface PredictionHistory {
  id: number;
  predicted_at: string;
  predicted_outcome: string | null;
  confidence: number | null;
  predicted_trophy_change: number | null;
  actual_outcome: string | null;
  actual_trophy_change: number | null;
}

export interface ModelStats {
  is_trained: boolean;
  samples: number | null;
  accuracy: number | null;
  f1: number | null;
  roc_auc: number | null;
  feature_count: number | null;
  feature_importance: Record<string, number> | null;
  class_distribution: { gain: number; loss: number } | null;
}

export interface DashboardStats {
  total_players: number;
  total_battles: number;
  total_predictions: number;
  last_sync: string | null;
  model_accuracy: number | null;
}

export interface SyncLog {
  id: number;
  started_at: string;
  completed_at: string | null;
  players_synced: number;
  battles_added: number;
  errors: number;
  status: string;
}

export type View = "overview" | "predict" | "players";
