"use client";

import { useEffect, useState } from "react";
import { api, type LogEntry } from "@/lib/api";
import { Card } from "@/components/ui";
import { Donut, PriorityBars } from "@/components/charts";

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    const load = () => api.getLogs(200).then(setLogs).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  const errors = logs.filter((l) => l.level === "error").length;

  const levelColor: Record<string, string> = {
    info: "var(--green)",
    error: "var(--red)",
    warn: "var(--amber)",
  };
  const levelData = ["info", "error", "warn"]
    .map((lv) => ({ name: lv, value: logs.filter((l) => l.level === lv).length, color: levelColor[lv] }))
    .filter((d) => d.value > 0);

  const sourceCounts = logs.reduce<Record<string, number>>((acc, l) => {
    acc[l.source] = (acc[l.source] ?? 0) + 1;
    return acc;
  }, {});
  const sourceData = Object.entries(sourceCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, value]) => ({ name, value, color: "var(--accent)" }));

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

      <div className="mx-auto w-full max-w-4xl px-6 py-6 md:px-8 space-y-4">
        <div className="grid gap-4 md:grid-cols-[220px_1fr]">
          <Card className="p-4">
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted">By level</div>
            <Donut data={levelData} centerValue={logs.length} centerLabel="events" height={124} inner={38} outer={56} />
            <div className="mt-1 flex flex-wrap items-center justify-center gap-x-3">
              {levelData.map((d) => (
                <span key={d.name} className="flex items-center gap-1 text-[11px] capitalize text-muted">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: d.color }} />
                  {d.name}
                </span>
              ))}
            </div>
          </Card>
          <Card className="p-4">
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted">By source</div>
            <PriorityBars data={sourceData} height={160} labelWidth={96} />
          </Card>
        </div>

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
