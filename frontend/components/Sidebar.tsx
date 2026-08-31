"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Overview", icon: "▦" },
  { href: "/inbox", label: "Inbox", icon: "✉" },
  { href: "/logs", label: "Activity", icon: "≣" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r bg-surface px-4 py-5">
      <div className="flex items-center gap-2.5 px-2 pb-6">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-accent-fg"
          style={{ background: "var(--accent)" }}
        >
          FTE
        </div>
        <div>
          <div className="text-sm font-semibold leading-tight">Digital FTE</div>
          <div className="text-xs text-muted leading-tight">AI Employee</div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-accent-soft text-accent"
                  : "text-muted hover:bg-surface-2 hover:text-fg"
              }`}
            >
              <span className="w-4 text-center opacity-80">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-lg border bg-surface-2 px-3 py-2.5 text-xs text-muted">
        <div className="font-medium text-fg">Self-hosted</div>
        Runs on your machine. Your data stays local.
      </div>
    </aside>
  );
}
