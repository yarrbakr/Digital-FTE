"use client";

import { useEffect, useState } from "react";
import { api, type LogEntry } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui";

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    const load = () => api.getLogs(200).then(setLogs).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <PageHeader title="Activity" subtitle="Every step your AI employee takes — the full audit trail" />
      <div className="mx-auto max-w-4xl px-6 py-6 md:px-8">
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
                    {l.item_id && <span className="text-[11px] text-muted">item #{l.item_id}</span>}
                    <span className="ml-auto text-[11px] text-muted">
                      {new Date(l.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-fg">{l.message}</p>
                </div>
              </li>
            ))}
            {logs.length === 0 && (
              <li className="px-5 py-16 text-center text-sm text-muted">No activity logged yet.</li>
            )}
          </ul>
        </Card>
      </div>
    </>
  );
}
