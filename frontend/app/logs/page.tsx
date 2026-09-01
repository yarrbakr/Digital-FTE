"use client";

import { useEffect, useState } from "react";
import { api, type LogEntry } from "@/lib/api";
import { Card } from "@/components/ui";

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    const load = () => api.getLogs(200).then(setLogs).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  const errors = logs.filter((l) => l.level === "error").length;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center gap-3 border-b px-6 py-4 md:px-8">
        <h1 className="text-base font-semibold">Activity</h1>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-muted">
          <span className="tabular-nums font-medium text-fg">{logs.length}</span> events
        </span>
        {errors > 0 && (
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
            style={{ background: "var(--red-soft)", color: "var(--red)" }}
          >
            <span className="tabular-nums">{errors}</span> errors
          </span>
        )}
      </header>

      <div className="mx-auto w-full max-w-4xl px-6 py-6 md:px-8">
        <Card>
          <ul className="divide-y">
            {logs.map((l) => (
              <li key={l.id} className="flex items-start gap-3 px-5 py-3">
                <span
                  className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{
                    background:
                      l.level === "error" ? "var(--red)" : l.level === "warn" ? "var(--amber)" : "var(--green)",
                  }}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-fg">{l.source}</span>
                    {l.item_id && <span className="text-[11px] text-muted">#{l.item_id}</span>}
                    <span className="ml-auto text-[11px] text-muted">
                      {new Date(l.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-fg">{l.message}</p>
                </div>
              </li>
            ))}
            {logs.length === 0 && (
              <li className="px-5 py-16 text-center text-sm text-muted">No activity yet.</li>
            )}
          </ul>
        </Card>
      </div>
    </div>
  );
}
