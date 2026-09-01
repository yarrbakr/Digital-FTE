"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Inbox, LayoutGrid, Settings } from "lucide-react";
import type { ComponentType } from "react";

const NAV: { href: string; label: string; Icon: ComponentType<{ size?: number }> }[] = [
  { href: "/", label: "Overview", Icon: LayoutGrid },
  { href: "/inbox", label: "Inbox", Icon: Inbox },
  { href: "/logs", label: "Activity", Icon: Activity },
  { href: "/settings", label: "Settings", Icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-16 shrink-0 flex-col items-center border-r bg-surface py-4">
      <Link
        href="/"
        className="flex h-9 w-9 items-center justify-center rounded-lg text-[11px] font-bold text-accent-fg"
        style={{ background: "var(--accent)" }}
        title="Digital FTE"
      >
        FTE
      </Link>

      <nav className="mt-6 flex flex-1 flex-col items-center gap-2">
        {NAV.map(({ href, label, Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              title={label}
              aria-label={label}
              className={`group relative flex h-10 w-10 items-center justify-center rounded-xl transition-colors ${
                active ? "bg-accent-soft text-accent" : "text-muted hover:bg-surface-2 hover:text-fg"
              }`}
            >
              <Icon size={19} />
              <span className="pointer-events-none absolute left-12 z-10 whitespace-nowrap rounded-md border bg-surface px-2 py-1 text-xs font-medium text-fg opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                {label}
              </span>
            </Link>
          );
        })}
      </nav>

      <span
        className="mt-auto h-2 w-2 rounded-full"
        style={{ background: "var(--green)" }}
        title="Self-hosted · running locally"
      />
    </aside>
  );
}
