"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type AppConfig, type Item, type ItemStatus, type LogEntry } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Button, Card, PriorityBadge, StatusBadge } from "@/components/ui";

const STAT_CARDS: { key: ItemStatus; label: string; hint: string; color: string }[] = [
  { key: "new", label: "To process", hint: "Waiting for the AI", color: "var(--slate)" },
  { key: "pending_approval", label: "Needs your approval", hint: "Drafts ready to review", color: "var(--amber)" },
  { key: "approved", label: "Queued to send", hint: "Approved, awaiting execution", color: "var(--blue)" },
  { key: "done", label: "Completed", hint: "Handled end-to-end", color: "var(--green)" },
];

export default function OverviewPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [online, setOnline] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [i, l, c] = await Promise.all([api.listItems(), api.getLogs(8), api.getConfig()]);
      setItems(i);
      setLogs(l);
      setConfig(c);
      setOnline(true);
    } catch {
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  const count = (s: ItemStatus) => items.filter((i) => i.status === s).length;

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    setError(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader title="Overview" subtitle="Your AI employee at a glance">
        <Button
          onClick={() => run("process", api.processItems)}
          disabled={busy !== null}
          variant="primary"
        >
          {busy === "process" ? "Processing…" : "Process new"}
        </Button>
        <Button
          onClick={() => run("execute", api.execute)}
          disabled={busy !== null}
          variant="success"
        >
          {busy === "execute" ? "Sending…" : "Execute approved"}
        </Button>
      </PageHeader>

      <div className="mx-auto max-w-6xl px-6 py-6 md:px-8">
        {!online && (
          <Banner tone="red">
            Can’t reach the backend at <code>{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</code>. Is it running?
          </Banner>
        )}
        {config && !config.api_key_set && online && (
          <Banner tone="amber">
            No AI provider key set. Add <code>LLM_API_KEY</code> to <code>backend/.env</code> so the AI can draft.
          </Banner>
        )}
        {error && <Banner tone="red">{error}</Banner>}

        {/* Stat grid */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {STAT_CARDS.map((s) => (
            <Card key={s.key} className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">{s.label}</span>
                <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
              </div>
              <div className="mt-3 text-3xl font-semibold tabular-nums">{count(s.key)}</div>
              <div className="mt-1 text-xs text-muted">{s.hint}</div>
            </Card>
          ))}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {/* Needs approval */}
          <Card className="lg:col-span-2">
            <div className="flex items-center justify-between border-b px-5 py-3.5">
              <h2 className="text-sm font-semibold">Waiting for your approval</h2>
              <Link href="/inbox" className="text-xs font-medium text-accent hover:underline">
                Open inbox →
              </Link>
            </div>
            <div className="divide-y">
              {items.filter((i) => i.status === "pending_approval").slice(0, 5).map((i) => (
                <Link
                  key={i.id}
                  href={`/inbox?item=${i.id}`}
                  className="flex items-center gap-3 px-5 py-3 hover:bg-surface-2"
                >
                  <PriorityBadge priority={i.priority} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{i.subject || "(no subject)"}</div>
                    <div className="truncate text-xs text-muted">{i.sender}</div>
                  </div>
                  <span className="text-xs text-muted">{i.channel}</span>
                </Link>
              ))}
              {items.filter((i) => i.status === "pending_approval").length === 0 && (
                <div className="px-5 py-10 text-center text-sm text-muted">
                  Nothing waiting. You’re all caught up. ✨
                </div>
              )}
            </div>
          </Card>

          {/* Recent activity */}
          <Card>
            <div className="border-b px-5 py-3.5">
              <h2 className="text-sm font-semibold">Recent activity</h2>
            </div>
            <ul className="divide-y">
              {logs.map((l) => (
                <li key={l.id} className="px-5 py-2.5">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: l.level === "error" ? "var(--red)" : "var(--green)" }}
                    />
                    <span className="text-xs font-medium text-muted">{l.source}</span>
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-xs text-fg">{l.message}</p>
                </li>
              ))}
              {logs.length === 0 && (
                <li className="px-5 py-10 text-center text-sm text-muted">No activity yet.</li>
              )}
            </ul>
          </Card>
        </div>

        {config && (
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-muted">
            <span>Provider: <span className="font-medium text-fg">{config.provider}</span></span>
            <span>Model: <span className="font-medium text-fg">{config.model}</span></span>
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: online ? "var(--green)" : "var(--red)" }} />
              {online ? "Backend connected" : "Backend offline"}
            </span>
          </div>
        )}
      </div>
    </>
  );
}

function Banner({ tone, children }: { tone: "red" | "amber"; children: React.ReactNode }) {
  const bg = tone === "red" ? "var(--red-soft)" : "var(--amber-soft)";
  const fg = tone === "red" ? "var(--red)" : "var(--amber)";
  return (
    <div className="mb-5 rounded-lg px-4 py-3 text-sm" style={{ background: bg, color: fg }}>
      {children}
    </div>
  );
}
