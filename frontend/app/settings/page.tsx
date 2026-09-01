"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type AppConfig, type Connection } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, Button } from "@/components/ui";

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
      if (typeof r.gmail === "number") parts.push(`Gmail: ${r.gmail} new`);
      if (typeof r.slack === "number") parts.push(`Slack: ${r.slack} new`);
      if (r.gmail_error) parts.push(`Gmail error: ${r.gmail_error}`);
      if (r.slack_error) parts.push(`Slack error: ${r.slack_error}`);
      setWatchMsg(parts.length ? parts.join(" · ") : "No connected channels to poll.");
    } catch (e) {
      setWatchMsg(e instanceof Error ? e.message : "Poll failed.");
    } finally {
      setWatching(false);
    }
  }

  return (
    <>
      <PageHeader title="Settings" subtitle="How this instance is configured">
        <Button variant="ghost" onClick={checkNow} disabled={watching}>
          {watching ? "Checking…" : "Check for new messages now"}
        </Button>
      </PageHeader>

      <div className="mx-auto max-w-3xl px-6 py-6 md:px-8 space-y-6">
        {watchMsg && (
          <div
            className="rounded-lg border px-4 py-2.5 text-sm"
            style={{ background: "var(--blue-soft)", color: "var(--blue)" }}
          >
            {watchMsg}
          </div>
        )}

        <Card className="p-6">
          <h2 className="text-sm font-semibold">Channels</h2>
          <p className="mt-0.5 text-sm text-muted">
            Connect a mailbox and a Slack workspace. The watcher polls them every{" "}
            {config ? `${config.poll_interval_seconds}s` : "few minutes"}
            {config?.scheduler_running ? " (running)." : " (scheduler off)."}
          </p>
          <div className="mt-4 space-y-4">
            <GmailConnect conn={gmail} onChange={refresh} />
            <SlackConnect conn={slack} onChange={refresh} />
          </div>
        </Card>

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
            <Row
              label="Poll interval"
              value={config ? `${config.poll_interval_seconds}s` : undefined}
            />
          </dl>
        </Card>

        <Card className="p-6">
          <h2 className="text-sm font-semibold">Storage</h2>
          <dl className="mt-4 grid grid-cols-1 gap-y-3">
            <Row label="Database" value={config?.database_url} mono />
          </dl>
          <p className="mt-3 text-xs text-muted">
            Embedded SQLite — your data never leaves this machine. Credentials are
            stored encrypted at rest.
          </p>
        </Card>
      </div>
    </>
  );
}

function GmailConnect({
  conn,
  onChange,
}: {
  conn?: Connection;
  onChange: () => void;
}) {
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
      setErr(e instanceof Error ? e.message : "Connection failed.");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    await api.deleteConnection("gmail").catch(() => {});
    onChange();
  }

  return (
    <ChannelBlock
      name="Gmail"
      conn={conn}
      onDisconnect={disconnect}
      onToggleForm={() => setOpen((v) => !v)}
      formOpen={open}
    >
      <p className="text-xs text-muted">
        Uses IMAP + an <strong>App Password</strong> (needs 2-Step Verification on
        the account). Reads unread mail; sends replies via SMTP.
      </p>
      <input
        className="fte-input"
        placeholder="you@gmail.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="off"
      />
      <input
        className="fte-input"
        placeholder="16-character app password"
        value={pw}
        onChange={(e) => setPw(e.target.value)}
        type="password"
        autoComplete="off"
      />
      {err && (
        <p className="text-xs" style={{ color: "var(--red)" }}>
          {err}
        </p>
      )}
      <div className="flex gap-2">
        <Button onClick={connect} disabled={busy || !email || !pw}>
          {busy ? "Verifying…" : "Connect Gmail"}
        </Button>
      </div>
    </ChannelBlock>
  );
}

function SlackConnect({
  conn,
  onChange,
}: {
  conn?: Connection;
  onChange: () => void;
}) {
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
      setErr(e instanceof Error ? e.message : "Connection failed.");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    await api.deleteConnection("slack").catch(() => {});
    onChange();
  }

  return (
    <ChannelBlock
      name="Slack"
      conn={conn}
      onDisconnect={disconnect}
      onToggleForm={() => setOpen((v) => !v)}
      formOpen={open}
    >
      <p className="text-xs text-muted">
        Paste a <strong>Bot User OAuth Token</strong> (<code>xoxb-…</code>). Invite
        the bot to any channel you want it to watch. Replies post in-thread.
      </p>
      <input
        className="fte-input"
        placeholder="xoxb-…"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        type="password"
        autoComplete="off"
      />
      {err && (
        <p className="text-xs" style={{ color: "var(--red)" }}>
          {err}
        </p>
      )}
      <div className="flex gap-2">
        <Button onClick={connect} disabled={busy || !token}>
          {busy ? "Verifying…" : "Connect Slack"}
        </Button>
      </div>
    </ChannelBlock>
  );
}

function ChannelBlock({
  name,
  conn,
  onDisconnect,
  onToggleForm,
  formOpen,
  children,
}: {
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
  const label = connected
    ? `Connected — ${conn?.name}`
    : error
      ? `Error — ${conn?.name}`
      : "Not connected";

  return (
    <div className="rounded-lg border bg-surface-2 px-4 py-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium">{name}</div>
          <div className="text-xs text-muted">{label}</div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-medium"
            style={{ background: `var(--${tone}-soft)`, color: `var(--${tone})` }}
          >
            {connected ? "Connected" : error ? "Error" : "Off"}
          </span>
          {conn ? (
            <Button variant="ghost" onClick={onDisconnect}>
              Disconnect
            </Button>
          ) : (
            <Button variant="ghost" onClick={onToggleForm}>
              {formOpen ? "Cancel" : "Connect"}
            </Button>
          )}
        </div>
      </div>
      {!conn && formOpen && <div className="mt-3 space-y-2">{children}</div>}
    </div>
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
