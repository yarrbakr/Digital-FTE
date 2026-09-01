"use client";

import { useCallback, useEffect, useState } from "react";
import { Database, Hash, Mail, RefreshCw, Sparkles } from "lucide-react";
import { api, type AppConfig, type Connection } from "@/lib/api";
import { Card } from "@/components/ui";
import { SmoothButton } from "@/components/ui/smooth-button";

export default function SettingsPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [watchMsg, setWatchMsg] = useState<string | null>(null);
  const [watching, setWatching] = useState(false);

  const refresh = useCallback(() => {
    api.getConfig().then(setConfig).catch(() => {});
    api.listConnections().then(setConnections).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const gmail = connections.find((c) => c.kind === "gmail");
  const slack = connections.find((c) => c.kind === "slack");

  async function checkNow() {
    setWatching(true);
    setWatchMsg(null);
    try {
      const r = await api.runWatch();
      const parts: string[] = [];
      if (typeof r.gmail === "number") parts.push(`Gmail +${r.gmail}`);
      if (typeof r.slack === "number") parts.push(`Slack +${r.slack}`);
      if (r.gmail_error) parts.push(`Gmail error: ${r.gmail_error}`);
      if (r.slack_error) parts.push(`Slack error: ${r.slack_error}`);
      setWatchMsg(parts.length ? parts.join(" · ") : "No connected channels.");
    } catch (e) {
      setWatchMsg(e instanceof Error ? e.message : "Poll failed.");
    } finally {
      setWatching(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center gap-4 border-b px-6 py-4 md:px-8">
        <h1 className="text-base font-semibold">Settings</h1>
        <div className="ml-auto">
          <SmoothButton variant="outline" onClick={checkNow} disabled={watching}>
            <RefreshCw className={watching ? "animate-spin" : ""} /> {watching ? "Checking" : "Check now"}
          </SmoothButton>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl px-6 py-6 md:px-8 space-y-4">
        {watchMsg && (
          <div className="rounded-lg border px-4 py-2.5 text-sm" style={{ background: "var(--blue-soft)", color: "var(--blue)" }}>
            {watchMsg}
          </div>
        )}

        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Channels</h2>
            <span
              className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium text-muted"
              title={config?.scheduler_running ? "Watching" : "Idle"}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${config?.scheduler_running ? "animate-pulse" : ""}`}
                style={{ background: config?.scheduler_running ? "var(--green)" : "var(--slate)" }}
              />
              {config ? `every ${config.poll_interval_seconds}s` : ""}
            </span>
          </div>
          <div className="space-y-3">
            <GmailConnect conn={gmail} onChange={refresh} />
            <SlackConnect conn={slack} onChange={refresh} />
          </div>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2">
          <Card className="p-5">
            <div className="mb-3 inline-flex items-center gap-2 text-sm font-semibold">
              <Sparkles size={15} className="text-accent" /> AI provider
            </div>
            <dl className="space-y-2.5">
              <Row label="Provider" value={config?.provider} />
              <Row label="Model" value={config?.model} mono />
              <Row
                label="API key"
                value={config ? (config.api_key_set ? "Set" : "Not set") : undefined}
                tone={config && !config.api_key_set ? "warn" : "ok"}
              />
            </dl>
          </Card>

          <Card className="p-5">
            <div className="mb-3 inline-flex items-center gap-2 text-sm font-semibold">
              <Database size={15} className="text-accent" /> Storage
            </div>
            <dl className="space-y-2.5">
              <Row label="Database" value={config?.database_url} mono />
              <Row label="Secrets" value="Encrypted at rest" tone="ok" />
            </dl>
            <p className="mt-3 text-xs text-muted">Local SQLite — data never leaves this machine.</p>
          </Card>
        </div>
      </div>
    </div>
  );
}

function GmailConnect({ conn, onChange }: { conn?: Connection; onChange: () => void }) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function connect() {
    setBusy(true);
    setErr(null);
    try {
      await api.connectGmail(email.trim(), pw);
      setOpen(false);
      setEmail("");
      setPw("");
      onChange();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ChannelBlock
      icon={<Mail size={16} />}
      name="Gmail"
      conn={conn}
      onDisconnect={async () => {
        await api.deleteConnection("gmail").catch(() => {});
        onChange();
      }}
      onToggleForm={() => setOpen((v) => !v)}
      formOpen={open}
    >
      <p className="text-xs text-muted">IMAP + App Password (needs 2-Step Verification).</p>
      <input className="fte-input" placeholder="you@gmail.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="off" />
      <input className="fte-input" placeholder="16-char app password" value={pw} onChange={(e) => setPw(e.target.value)} type="password" autoComplete="off" />
      {err && <p className="text-xs" style={{ color: "var(--red)" }}>{err}</p>}
      <SmoothButton variant="primary" size="sm" onClick={connect} disabled={busy || !email || !pw}>
        {busy ? "Verifying…" : "Connect"}
      </SmoothButton>
    </ChannelBlock>
  );
}

function SlackConnect({ conn, onChange }: { conn?: Connection; onChange: () => void }) {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function connect() {
    setBusy(true);
    setErr(null);
    try {
      await api.connectSlack(token.trim());
      setOpen(false);
      setToken("");
      onChange();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ChannelBlock
      icon={<Hash size={16} />}
      name="Slack"
      conn={conn}
      onDisconnect={async () => {
        await api.deleteConnection("slack").catch(() => {});
        onChange();
      }}
      onToggleForm={() => setOpen((v) => !v)}
      formOpen={open}
    >
      <p className="text-xs text-muted">Bot User OAuth Token (<code>xoxb-…</code>); invite the bot to a channel.</p>
      <input className="fte-input" placeholder="xoxb-…" value={token} onChange={(e) => setToken(e.target.value)} type="password" autoComplete="off" />
      {err && <p className="text-xs" style={{ color: "var(--red)" }}>{err}</p>}
      <SmoothButton variant="primary" size="sm" onClick={connect} disabled={busy || !token}>
        {busy ? "Verifying…" : "Connect"}
      </SmoothButton>
    </ChannelBlock>
  );
}

function ChannelBlock({
  icon,
  name,
  conn,
  onDisconnect,
  onToggleForm,
  formOpen,
  children,
}: {
  icon: React.ReactNode;
  name: string;
  conn?: Connection;
  onDisconnect: () => void;
  onToggleForm: () => void;
  formOpen: boolean;
  children: React.ReactNode;
}) {
  const connected = conn?.status === "connected";
  const error = conn?.status === "error";
  const tone = connected ? "green" : error ? "red" : "slate";

  return (
    <div className="rounded-lg border bg-surface-2 px-4 py-3">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg text-muted" style={{ background: "var(--surface)" }}>
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium">{name}</div>
          <div className="truncate text-xs text-muted">{conn?.name ?? "Not connected"}</div>
        </div>
        <span className="h-2 w-2 rounded-full" style={{ background: `var(--${tone})` }} title={conn?.status ?? "off"} />
        {conn ? (
          <SmoothButton variant="ghost" size="sm" onClick={onDisconnect}>Disconnect</SmoothButton>
        ) : (
          <SmoothButton variant="ghost" size="sm" onClick={onToggleForm}>{formOpen ? "Cancel" : "Connect"}</SmoothButton>
        )}
      </div>
      {!conn && formOpen && <div className="mt-3 space-y-2">{children}</div>}
    </div>
  );
}

function Row({ label, value, mono, tone }: { label: string; value?: string; mono?: boolean; tone?: "warn" | "ok" }) {
  const color = tone === "warn" ? "var(--amber)" : tone === "ok" ? "var(--green)" : undefined;
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className={`truncate text-sm font-medium ${mono ? "font-mono text-xs" : ""}`} style={color ? { color } : undefined}>
        {value ?? "—"}
      </dd>
    </div>
  );
}
