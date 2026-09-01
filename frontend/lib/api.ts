// Thin client for the Digital FTE backend API.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export type ItemStatus =
  | "new"
  | "drafted"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "done"
  | "failed";

export type Priority = "high" | "medium" | "low";

export interface Draft {
  id: number;
  provider: string;
  model: string;
  action_type: string;
  content: string;
  reasoning: string;
  created_at: string;
}

export interface Item {
  id: number;
  channel: string;
  external_id: string;
  subject: string;
  body: string;
  sender: string;
  priority: Priority;
  status: ItemStatus;
  received_at: string;
  created_at: string;
}

export interface ItemDetail extends Item {
  drafts: Draft[];
}

export interface LogEntry {
  id: number;
  level: string;
  source: string;
  message: string;
  item_id: number | null;
  created_at: string;
}

export interface AppConfig {
  provider: string;
  model: string;
  api_key_set: boolean;
  poll_interval_seconds: number;
  database_url: string;
  scheduler_enabled: boolean;
  scheduler_running: boolean;
}

export interface ThroughputPoint {
  date: string;
  label: string;
  count: number;
  gmail: number;
  slack: number;
}

export interface Stats {
  total: number;
  pending_approval: number;
  queued: number;
  handled: number;
  new: number;
  failed: number;
  approval_rate: number;
  by_status: Record<ItemStatus, number>;
  by_priority: Record<Priority, number>;
  by_channel: Record<string, number>;
  throughput: ThroughputPoint[];
}

export interface Connection {
  id: number;
  kind: string; // "gmail" | "slack" | "provider"
  name: string;
  status: string; // "connected" | "error" | "disconnected"
  updated_at: string;
}

export interface WatchResult {
  gmail?: number;
  slack?: number;
  gmail_error?: string;
  slack_error?: string;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getConfig: () => req<AppConfig>("/api/config"),
  listItems: (status?: string) =>
    req<Item[]>(`/api/items${status ? `?status=${status}` : ""}`),
  getItem: (id: number) => req<ItemDetail>(`/api/items/${id}`),
  createItem: (body: {
    channel: string;
    subject: string;
    body: string;
    sender: string;
  }) => req<Item>("/api/items", { method: "POST", body: JSON.stringify(body) }),
  processItems: () =>
    req<{ processed: number; errors: number; found: number }>(
      "/api/items/process",
      { method: "POST" },
    ),
  approve: (id: number) =>
    req<Item>(`/api/items/${id}/approve`, { method: "POST" }),
  reject: (id: number) =>
    req<Item>(`/api/items/${id}/reject`, { method: "POST" }),
  editDraft: (id: number, content: string) =>
    req<ItemDetail>(`/api/items/${id}/draft`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),
  executeItem: (id: number) =>
    req<ItemDetail>(`/api/items/${id}/execute`, { method: "POST" }),
  execute: () =>
    req<{ done: number; failed: number; found: number }>("/api/items/execute", {
      method: "POST",
    }),
  getLogs: (limit = 50) => req<LogEntry[]>(`/api/logs?limit=${limit}`),
  getStats: () => req<Stats>("/api/stats"),

  listConnections: () => req<Connection[]>("/api/connections"),
  connectGmail: (email: string, app_password: string) =>
    req<Connection>("/api/connections/gmail", {
      method: "POST",
      body: JSON.stringify({ email, app_password }),
    }),
  connectSlack: (bot_token: string) =>
    req<Connection>("/api/connections/slack", {
      method: "POST",
      body: JSON.stringify({ bot_token }),
    }),
  deleteConnection: (kind: string) =>
    req<{ deleted: string }>(`/api/connections/${kind}`, { method: "DELETE" }),
  runWatch: () => req<WatchResult>("/api/watch/run", { method: "POST" }),
};
