import type {
  DashboardStats,
  ModelStats,
  Player,
  PlayerDetail,
  Prediction,
  PredictionHistory,
  SyncLog,
} from "../types";

const BASE = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export function fetchPlayers(): Promise<Player[]> {
  return request("/players/");
}

export function fetchPlayer(tag: string): Promise<PlayerDetail> {
  const encoded = encodeURIComponent(tag);
  return request(`/players/${encoded}`);
}

export function addPlayer(tag: string): Promise<Player> {
  return request("/players/", {
    method: "POST",
    body: JSON.stringify({ tag }),
  });
}

export function removePlayer(tag: string): Promise<void> {
  const encoded = encodeURIComponent(tag);
  return request(`/players/${encoded}`, { method: "DELETE" });
}

export function fetchPrediction(tag: string): Promise<Prediction> {
  const encoded = encodeURIComponent(tag);
  return request(`/predict/${encoded}`);
}

export function fetchPredictionHistory(tag: string): Promise<PredictionHistory[]> {
  const encoded = encodeURIComponent(tag);
  return request(`/predict/${encoded}/history`);
}

export function fetchModelStats(): Promise<ModelStats> {
  return request("/stats/model");
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return request("/stats/dashboard");
}

export function fetchSyncLogs(): Promise<SyncLog[]> {
  return request("/stats/sync-logs");
}
