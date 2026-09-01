"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Play, Send } from "lucide-react";
import { api, type AppConfig, type Item, type Stats } from "@/lib/api";
import { Card } from "@/components/ui";
import { SmoothButton } from "@/components/ui/smooth-button";
import { Donut, Gauge, MiniBars, PriorityBars, ThroughputChart } from "@/components/charts";

export default function OverviewPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [pending, setPending] = useState<Item[]>([]);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [online, setOnline] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [s, p, c] = await Promise.all([
        api.getStats(),
        api.listItems("pending_approval"),
        api.getConfig(),
      ]);
      setStats(s);
      setPending(p);
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

  const spark = (stats?.throughput ?? []).map((t) => t.count);
  const statusData = stats
    ? [
        { name: "done", value: stats.by_status.done, color: "var(--green)" },
        { name: "pending", value: stats.by_status.pending_approval, color: "var(--amber)" },
        { name: "approved", value: stats.by_status.approved, color: "var(--blue)" },
        { name: "new", value: stats.by_status.new, color: "var(--slate)" },
        { name: "failed", value: stats.by_status.failed, color: "var(--red)" },
      ].filter((d) => d.value > 0)
    : [];
  const channelData = stats
    ? [
        { name: "gmail", value: stats.by_channel.gmail ?? 0, color: "var(--accent)" },
        { name: "slack", value: stats.by_channel.slack ?? 0, color: "var(--green)" },
      ].filter((d) => d.value > 0)
    : [];
  const priorityData = stats
    ? [
        { name: "High", value: stats.by_priority.high, color: "var(--red)" },
        { name: "Medium", value: stats.by_priority.medium, color: "var(--amber)" },
        { name: "Low", value: stats.by_priority.low, color: "var(--slate)" },
      ]
    : [];

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <header className="flex items-center gap-4 border-b px-6 py-4 md:px-8">
        <h1 className="text-base font-semibold">Overview</h1>
        <span
          className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-muted"
          title={config?.scheduler_running ? "Watching channels" : "Scheduler off"}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${config?.scheduler_running ? "animate-pulse" : ""}`}
            style={{ background: config?.scheduler_running ? "var(--green)" : "var(--slate)" }}
          />
          {config?.scheduler_running ? "Watching" : "Idle"}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <SmoothButton variant="primary" onClick={() => run("process", api.processItems)} disabled={busy !== null}>
            <Play /> {busy === "process" ? "Processing" : "Process"}
          </SmoothButton>
          <SmoothButton variant="success" onClick={() => run("execute", api.execute)} disabled={busy !== null}>
            <Send /> {busy === "execute" ? "Sending" : "Execute"}
          </SmoothButton>
        </div>
      </header>

      <div className="mx-auto w-full max-w-7xl px-6 py-6 md:px-8">
        {!online && (
          <Banner tone="red">Backend offline — start it on <code>:8000</code>.</Banner>
        )}
        {config && !config.api_key_set && online && (
          <Banner tone="amber">No AI key set. Add <code>LLM_API_KEY</code> to <code>backend/.env</code>.</Banner>
        )}
        {error && <Banner tone="red">{error}</Banner>}

        {/* KPI tiles */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Kpi label="Handled" value={stats?.handled ?? 0}>
            <MiniBars data={spark} color="var(--green)" />
          </Kpi>
          <Kpi label="Pending" value={stats?.pending_approval ?? 0}>
            <MiniBars data={spark} color="var(--amber)" />
          </Kpi>
          <Kpi label="Queued" value={stats?.queued ?? 0}>
            <MiniBars data={spark} color="var(--blue)" />
          </Kpi>
          <Kpi label="Approval rate" value={`${stats?.approval_rate ?? 0}%`}>
            <Gauge value={stats?.approval_rate ?? 0} color="var(--accent)" />
          </Kpi>
        </div>

        {/* Throughput + Status */}
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <ChartCard title="Throughput" hint="14 days" className="lg:col-span-2">
            <ThroughputChart data={stats?.throughput ?? []} />
            <Legend items={[{ label: "Gmail", color: "var(--accent)" }, { label: "Slack", color: "var(--green)" }]} />
          </ChartCard>
          <ChartCard title="Status">
            <Donut data={statusData} centerValue={stats?.total ?? 0} centerLabel="total" />
            <Legend items={statusData.map((d) => ({ label: d.name, color: d.color }))} />
          </ChartCard>
        </div>

        {/* Priority + Channels + Needs approval */}
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <ChartCard title="Priority">
            <PriorityBars data={priorityData} />
          </ChartCard>
          <ChartCard title="Channels">
            <Donut data={channelData} centerValue={(stats?.by_channel.gmail ?? 0) + (stats?.by_channel.slack ?? 0)} centerLabel="items" />
            <Legend items={channelData.map((d) => ({ label: d.name, color: d.color }))} />
          </ChartCard>

          <Card className="flex flex-col">
            <div className="flex items-center justify-between border-b px-5 py-3.5">
              <h2 className="text-sm font-semibold">Needs approval</h2>
              <span
                className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                style={{ background: "var(--amber-soft)", color: "var(--amber)" }}
              >
                {pending.length}
              </span>
            </div>
            <div className="flex-1 divide-y">
              {pending.slice(0, 5).map((i) => (
                <Link key={i.id} href={`/inbox?item=${i.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-surface-2">
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ background: i.priority === "high" ? "var(--red)" : i.priority === "medium" ? "var(--amber)" : "var(--slate)" }}
                  />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium">{i.subject || "(no subject)"}</span>
                  <span className="text-[11px] uppercase text-muted">{i.channel}</span>
                </Link>
              ))}
              {pending.length === 0 && (
                <div className="flex flex-1 items-center justify-center px-5 py-10 text-center text-sm text-muted">
                  All caught up ✨
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, children }: { label: string; value: number | string; children: React.ReactNode }) {
  return (
    <Card className="p-4">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 text-3xl font-semibold tabular-nums">{value}</div>
      <div className="mt-2">{children}</div>
    </Card>
  );
}

function ChartCard({
  title,
  hint,
  className = "",
  children,
}: {
  title: string;
  hint?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Card className={`p-5 ${className}`}>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold">{title}</h2>
        {hint && <span className="text-[11px] uppercase tracking-wider text-muted">{hint}</span>}
      </div>
      {children}
    </Card>
  );
}

function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <div className="mt-3 flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
      {items.map((it) => (
        <span key={it.label} className="flex items-center gap-1.5 text-xs capitalize text-muted">
          <span className="h-2 w-2 rounded-full" style={{ background: it.color }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}

function Banner({ tone, children }: { tone: "red" | "amber"; children: React.ReactNode }) {
  const bg = tone === "red" ? "var(--red-soft)" : "var(--amber-soft)";
  const fg = tone === "red" ? "var(--red)" : "var(--amber)";
  return (
    <div className="mb-4 rounded-lg px-4 py-3 text-sm" style={{ background: bg, color: fg }}>
      {children}
    </div>
  );
}
