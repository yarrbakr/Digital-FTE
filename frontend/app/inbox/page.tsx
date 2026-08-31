"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Item, type ItemDetail } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Button, Card, PriorityBadge, StatusBadge } from "@/components/ui";

const FILTERS = [
  { key: "", label: "All" },
  { key: "pending_approval", label: "Pending" },
  { key: "new", label: "New" },
  { key: "done", label: "Done" },
];

export default function InboxPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setItems(await api.listItems(filter || undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [filter]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  // open ?item=ID on first load
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

  return (
    <>
      <PageHeader title="Inbox" subtitle="Review what your AI employee drafted, then approve or reject">
        <Button variant="primary" onClick={() => setShowNew(true)}>
          + Simulate incoming
        </Button>
      </PageHeader>

      <div className="grid gap-0 md:grid-cols-[minmax(300px,380px)_1fr] md:h-[calc(100vh-81px)]">
        {/* List */}
        <div className="border-r md:overflow-y-auto">
          <div className="flex gap-1 border-b bg-surface px-4 py-2.5">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  filter === f.key ? "bg-accent-soft text-accent" : "text-muted hover:bg-surface-2"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="divide-y">
            {items.map((i) => (
              <button
                key={i.id}
                onClick={() => setSelectedId(i.id)}
                className={`flex w-full items-start gap-3 px-4 py-3 text-left transition-colors ${
                  selectedId === i.id ? "bg-accent-soft" : "hover:bg-surface-2"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <PriorityBadge priority={i.priority} />
                    <span className="text-[11px] uppercase tracking-wide text-muted">{i.channel}</span>
                  </div>
                  <div className="mt-1 truncate text-sm font-medium">{i.subject || "(no subject)"}</div>
                  <div className="truncate text-xs text-muted">{i.sender || "unknown sender"}</div>
                </div>
                <StatusBadge status={i.status} />
              </button>
            ))}
            {items.length === 0 && (
              <div className="px-4 py-16 text-center text-sm text-muted">
                No items here.<br />Try “Simulate incoming”.
              </div>
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="md:overflow-y-auto">
          {error && (
            <div className="m-4 rounded-lg px-4 py-3 text-sm" style={{ background: "var(--red-soft)", color: "var(--red)" }}>
              {error}
            </div>
          )}
          {!detail ? (
            <div className="flex h-full items-center justify-center p-10 text-center text-sm text-muted">
              Select an item to review its draft.
            </div>
          ) : (
            <div className="mx-auto max-w-2xl px-6 py-6">
              <div className="flex flex-wrap items-center gap-2">
                <PriorityBadge priority={detail.priority} />
                <StatusBadge status={detail.status} />
                <span className="text-xs text-muted">
                  {detail.channel} · from {detail.sender || "unknown"}
                </span>
              </div>
              <h2 className="mt-3 text-lg font-semibold">{detail.subject || "(no subject)"}</h2>

              {/* Original message */}
              <Card className="mt-4 p-4">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
                  Original message
                </div>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{detail.body}</p>
              </Card>

              {/* Draft */}
              {detail.drafts.length > 0 ? (
                <Card className="mt-4 p-4" >
                  <div className="mb-2 flex items-center justify-between">
                    <div className="text-xs font-semibold uppercase tracking-wide text-accent">
                      AI draft · {detail.drafts[detail.drafts.length - 1].action_type}
                    </div>
                    <span className="text-[11px] text-muted">
                      {detail.drafts[detail.drafts.length - 1].provider}/{detail.drafts[detail.drafts.length - 1].model}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {detail.drafts[detail.drafts.length - 1].content}
                  </p>
                  {detail.drafts[detail.drafts.length - 1].reasoning && (
                    <div className="mt-3 border-t pt-3 text-xs text-muted">
                      <span className="font-medium">Why: </span>
                      {detail.drafts[detail.drafts.length - 1].reasoning}
                    </div>
                  )}
                </Card>
              ) : (
                <Card className="mt-4 p-4 text-sm text-muted">
                  No draft yet — run <span className="font-medium text-fg">Process new</span> on the Overview.
                </Card>
              )}

              {/* Actions */}
              {detail.status === "pending_approval" && (
                <div className="mt-5 flex gap-2">
                  <Button variant="success" disabled={busy} onClick={() => act(() => api.approve(detail.id))}>
                    ✓ Approve & send
                  </Button>
                  <Button variant="danger" disabled={busy} onClick={() => act(() => api.reject(detail.id))}>
                    ✕ Reject
                  </Button>
                </div>
              )}
              {detail.status === "approved" && (
                <div className="mt-5 flex items-center gap-2">
                  <Button variant="primary" disabled={busy} onClick={() => act(api.execute)}>
                    Execute now
                  </Button>
                  <span className="text-xs text-muted">Approved — will be sent on the next run.</span>
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
    </>
  );
}

function NewItemModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (id: number) => void;
}) {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <Card className="w-full max-w-lg p-6" >
        <div onClick={(e) => e.stopPropagation()}>
          <h3 className="text-base font-semibold">Simulate an incoming message</h3>
          <p className="mt-0.5 text-sm text-muted">
            Drop a test message into the pipeline — no Gmail/Slack needed.
          </p>

          <div className="mt-4 space-y-3">
            <div className="flex gap-2">
              {["gmail", "slack"].map((c) => (
                <button
                  key={c}
                  onClick={() => setChannel(c)}
                  className={`rounded-lg border px-3 py-1.5 text-sm capitalize ${
                    channel === c ? "border-transparent bg-accent-soft text-accent" : "hover:bg-surface-2"
                  }`}
                >
                  {c}
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
            <Button onClick={onClose}>Cancel</Button>
            <Button variant="primary" disabled={busy} onClick={submit}>
              {busy ? "Adding…" : "Add to inbox"}
            </Button>
          </div>
        </div>
      </Card>
      <style>{`.fte-input{width:100%;border:1px solid var(--border);background:var(--surface);color:var(--fg);border-radius:0.5rem;padding:0.5rem 0.75rem;font-size:0.875rem;outline:none}.fte-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}`}</style>
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
