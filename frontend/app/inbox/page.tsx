"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, Hash, Mail, Plus, Send, Sparkles, X } from "lucide-react";
import { api, type Item, type ItemDetail, type ItemStatus } from "@/lib/api";
import { Card, PriorityBadge, StatusBadge } from "@/components/ui";
import { SmoothButton } from "@/components/ui/smooth-button";

const FILTERS: { key: string; label: string; match?: ItemStatus }[] = [
  { key: "", label: "All" },
  { key: "pending_approval", label: "Pending", match: "pending_approval" },
  { key: "new", label: "New", match: "new" },
  { key: "done", label: "Done", match: "done" },
];

function ChannelIcon({ channel, className = "" }: { channel: string; className?: string }) {
  if (channel === "slack") return <Hash className={className} size={14} />;
  return <Mail className={className} size={14} />;
}

export default function InboxPage() {
  const [all, setAll] = useState<Item[]>([]);
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setAll(await api.listItems());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("item");
    if (id) setSelectedId(Number(id));
  }, []);

  useEffect(() => {
    if (selectedId == null) {
      setDetail(null);
      return;
    }
    api.getItem(selectedId).then(setDetail).catch(() => setDetail(null));
  }, [selectedId]);

  const items = useMemo(
    () => (filter ? all.filter((i) => i.status === filter) : all),
    [all, filter],
  );
  const countFor = (m?: ItemStatus) => (m ? all.filter((i) => i.status === m).length : all.length);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      if (selectedId != null) setDetail(await api.getItem(selectedId));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  const latestDraft = detail?.drafts.at(-1);

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center gap-4 border-b px-6 py-4 md:px-8">
        <h1 className="text-base font-semibold">Inbox</h1>
        <div className="flex items-center gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filter === f.key ? "bg-accent-soft text-accent" : "text-muted hover:bg-surface-2"
              }`}
            >
              {f.label}
              <span className="tabular-nums opacity-70">{countFor(f.match)}</span>
            </button>
          ))}
        </div>
        <div className="ml-auto">
          <SmoothButton variant="outline" onClick={() => setShowNew(true)}>
            <Plus /> Simulate
          </SmoothButton>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 md:grid-cols-[minmax(300px,380px)_1fr]">
        {/* List */}
        <div className="min-h-0 overflow-y-auto border-r">
          <div className="divide-y">
            {items.map((i) => (
              <button
                key={i.id}
                onClick={() => setSelectedId(i.id)}
                className={`flex w-full items-center gap-3 px-4 py-3 text-left transition-colors ${
                  selectedId === i.id ? "bg-accent-soft" : "hover:bg-surface-2"
                }`}
              >
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted"
                  style={{ background: "var(--surface-2)" }}
                >
                  <ChannelIcon channel={i.channel} />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{i.subject || "(no subject)"}</div>
                  <div className="truncate text-xs text-muted">{i.sender || "unknown"}</div>
                </div>
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  title={i.priority}
                  style={{
                    background:
                      i.priority === "high" ? "var(--red)" : i.priority === "medium" ? "var(--amber)" : "var(--slate)",
                  }}
                />
              </button>
            ))}
            {items.length === 0 && (
              <div className="px-4 py-16 text-center text-sm text-muted">Nothing here.</div>
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="min-h-0 overflow-y-auto">
          {error && (
            <div className="m-4 rounded-lg px-4 py-3 text-sm" style={{ background: "var(--red-soft)", color: "var(--red)" }}>
              {error}
            </div>
          )}
          {!detail ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 p-10 text-center text-sm text-muted">
              <Sparkles size={28} className="opacity-40" />
              Select an item to review.
            </div>
          ) : (
            <div className="mx-auto max-w-2xl px-6 py-6">
              <div className="flex flex-wrap items-center gap-2">
                <PriorityBadge priority={detail.priority} />
                <StatusBadge status={detail.status} />
                <span className="inline-flex items-center gap-1.5 text-xs text-muted">
                  <ChannelIcon channel={detail.channel} /> {detail.sender || "unknown"}
                </span>
              </div>
              <h2 className="mt-3 text-lg font-semibold">{detail.subject || "(no subject)"}</h2>

              <Card className="mt-4 p-4">
                <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted">Original</div>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{detail.body}</p>
              </Card>

              {latestDraft ? (
                <Card className="mt-4 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-accent">
                      <Sparkles size={13} /> AI draft · {latestDraft.action_type}
                    </div>
                    <span className="text-[11px] text-muted">{latestDraft.provider}/{latestDraft.model}</span>
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{latestDraft.content}</p>
                  {latestDraft.reasoning && (
                    <div className="mt-3 border-t pt-3 text-xs text-muted">
                      <span className="font-medium">Why: </span>
                      {latestDraft.reasoning}
                    </div>
                  )}
                </Card>
              ) : (
                <Card className="mt-4 p-4 text-sm text-muted">
                  {detail.status === "done"
                    ? "Triaged — the AI judged this needs no reply."
                    : detail.status === "new"
                      ? "Not processed yet — hit Process on the Overview."
                      : "No draft."}
                </Card>
              )}

              {detail.status === "pending_approval" && (
                <div className="mt-5 flex gap-2">
                  <SmoothButton variant="success" disabled={busy} onClick={() => act(() => api.approve(detail.id))}>
                    <Check /> Approve
                  </SmoothButton>
                  <SmoothButton variant="danger" disabled={busy} onClick={() => act(() => api.reject(detail.id))}>
                    <X /> Reject
                  </SmoothButton>
                </div>
              )}
              {detail.status === "approved" && (
                <div className="mt-5 flex items-center gap-3">
                  <SmoothButton variant="primary" disabled={busy} onClick={() => act(api.execute)}>
                    <Send /> Execute now
                  </SmoothButton>
                  <span className="text-xs text-muted">Queued for the next run.</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {showNew && (
        <NewItemModal
          onClose={() => setShowNew(false)}
          onCreated={async (id) => {
            setShowNew(false);
            await refresh();
            setSelectedId(id);
          }}
        />
      )}
    </div>
  );
}

function NewItemModal({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const [channel, setChannel] = useState("gmail");
  const [sender, setSender] = useState("client@acme.com");
  const [subject, setSubject] = useState("URGENT: invoice #4471 overdue");
  const [body, setBody] = useState(
    "Hi, our invoice #4471 for $12,000 is 5 days overdue. Please confirm payment today or we pause the project. Thanks, Dana.",
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      const item = await api.createItem({ channel, sender, subject, body });
      onCreated(item.id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <Card className="w-full max-w-lg p-6" >
        <div onClick={(e) => e.stopPropagation()}>
          <h3 className="text-base font-semibold">Simulate a message</h3>
          <p className="mt-0.5 text-sm text-muted">Drop a test message into the pipeline — no channel needed.</p>

          <div className="mt-4 space-y-3">
            <div className="flex gap-2">
              {(["gmail", "slack"] as const).map((c) => (
                <button
                  key={c}
                  onClick={() => setChannel(c)}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm capitalize ${
                    channel === c ? "border-transparent bg-accent-soft text-accent" : "hover:bg-surface-2"
                  }`}
                >
                  <ChannelIcon channel={c} /> {c}
                </button>
              ))}
            </div>
            <Field label="From">
              <input className="fte-input" value={sender} onChange={(e) => setSender(e.target.value)} />
            </Field>
            <Field label="Subject">
              <input className="fte-input" value={subject} onChange={(e) => setSubject(e.target.value)} />
            </Field>
            <Field label="Message">
              <textarea className="fte-input min-h-24" value={body} onChange={(e) => setBody(e.target.value)} />
            </Field>
          </div>

          {err && <p className="mt-3 text-sm" style={{ color: "var(--red)" }}>{err}</p>}

          <div className="mt-5 flex justify-end gap-2">
            <SmoothButton variant="ghost" onClick={onClose}>Cancel</SmoothButton>
            <SmoothButton variant="primary" disabled={busy} onClick={submit}>
              {busy ? "Adding…" : "Add to inbox"}
            </SmoothButton>
          </div>
        </div>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-muted">{label}</span>
      {children}
    </label>
  );
}
