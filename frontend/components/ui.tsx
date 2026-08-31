import type { ItemStatus, Priority } from "@/lib/api";

const STATUS_STYLE: Record<ItemStatus, { label: string; bg: string; fg: string }> = {
  new: { label: "New", bg: "var(--slate-soft)", fg: "var(--slate)" },
  drafted: { label: "Drafted", bg: "var(--blue-soft)", fg: "var(--blue)" },
  pending_approval: { label: "Pending", bg: "var(--amber-soft)", fg: "var(--amber)" },
  approved: { label: "Approved", bg: "var(--blue-soft)", fg: "var(--blue)" },
  rejected: { label: "Rejected", bg: "var(--slate-soft)", fg: "var(--slate)" },
  done: { label: "Done", bg: "var(--green-soft)", fg: "var(--green)" },
  failed: { label: "Failed", bg: "var(--red-soft)", fg: "var(--red)" },
};

const PRIORITY_STYLE: Record<Priority, { label: string; bg: string; fg: string }> = {
  high: { label: "High", bg: "var(--red-soft)", fg: "var(--red)" },
  medium: { label: "Medium", bg: "var(--amber-soft)", fg: "var(--amber)" },
  low: { label: "Low", bg: "var(--slate-soft)", fg: "var(--slate)" },
};

export function StatusBadge({ status }: { status: ItemStatus }) {
  const s = STATUS_STYLE[status] ?? STATUS_STYLE.new;
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ background: s.bg, color: s.fg }}
    >
      {s.label}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  const s = PRIORITY_STYLE[priority] ?? PRIORITY_STYLE.medium;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ background: s.bg, color: s.fg }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: s.fg }} />
      {s.label}
    </span>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border bg-surface shadow-[0_1px_2px_rgba(16,24,40,0.04)] ${className}`}
    >
      {children}
    </div>
  );
}

type BtnVariant = "primary" | "ghost" | "danger" | "success";

export function Button({
  children,
  variant = "ghost",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant }) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";
  const variants: Record<BtnVariant, string> = {
    primary: "bg-accent text-accent-fg hover:opacity-90",
    ghost: "border bg-surface text-fg hover:bg-surface-2",
    danger: "border text-[var(--red)] hover:bg-[var(--red-soft)]",
    success: "text-white hover:opacity-90",
  };
  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      style={variant === "success" ? { background: "var(--green)" } : undefined}
      {...props}
    >
      {children}
    </button>
  );
}

export function channelIcon(channel: string): string {
  if (channel === "slack") return "#";
  if (channel === "gmail") return "@";
  return "•";
}
