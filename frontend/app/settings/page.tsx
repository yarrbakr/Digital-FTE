"use client";

import { useEffect, useState } from "react";
import { api, type AppConfig } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui";

export default function SettingsPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    api.getConfig().then(setConfig).catch(() => {});
  }, []);

  return (
    <>
      <PageHeader title="Settings" subtitle="How this instance is configured" />
      <div className="mx-auto max-w-3xl px-6 py-6 md:px-8 space-y-6">
        <Card className="p-6">
          <h2 className="text-sm font-semibold">AI provider</h2>
          <p className="mt-0.5 text-sm text-muted">
            Bring your own provider — configured in <code>backend/.env</code>.
          </p>
          <dl className="mt-4 grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-2">
            <Row label="Provider" value={config?.provider} />
            <Row label="Model" value={config?.model} />
            <Row
              label="API key"
              value={config ? (config.api_key_set ? "Set ✓" : "Not set") : undefined}
              tone={config && !config.api_key_set ? "warn" : undefined}
            />
            <Row label="Poll interval" value={config ? `${config.poll_interval_seconds}s` : undefined} />
          </dl>
        </Card>

        <Card className="p-6">
          <h2 className="text-sm font-semibold">Storage</h2>
          <dl className="mt-4 grid grid-cols-1 gap-y-3">
            <Row label="Database" value={config?.database_url} mono />
          </dl>
          <p className="mt-3 text-xs text-muted">
            Embedded SQLite — your data never leaves this machine.
          </p>
        </Card>

        <Card className="p-6">
          <h2 className="text-sm font-semibold">Channels</h2>
          <div className="mt-4 space-y-3">
            <ChannelRow name="Gmail" note="Connect via Google OAuth (coming next)" />
            <ChannelRow name="Slack" note="Connect a Slack bot token (coming next)" />
          </div>
        </Card>
      </div>
    </>
  );
}

function Row({
  label,
  value,
  mono,
  tone,
}: {
  label: string;
  value?: string;
  mono?: boolean;
  tone?: "warn";
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted">{label}</dt>
      <dd
        className={`mt-0.5 text-sm ${mono ? "font-mono text-xs" : "font-medium"}`}
        style={tone === "warn" ? { color: "var(--amber)" } : undefined}
      >
        {value ?? "—"}
      </dd>
    </div>
  );
}

function ChannelRow({ name, note }: { name: string; note: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border bg-surface-2 px-4 py-3">
      <div>
        <div className="text-sm font-medium">{name}</div>
        <div className="text-xs text-muted">{note}</div>
      </div>
      <span
        className="rounded-full px-2.5 py-0.5 text-xs font-medium"
        style={{ background: "var(--slate-soft)", color: "var(--slate)" }}
      >
        Not connected
      </span>
    </div>
  );
}
