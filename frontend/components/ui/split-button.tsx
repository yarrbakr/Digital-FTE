"use client";

// A split action button: a primary action on the left + a chevron that opens a
// small menu of secondary actions. Used for "Approve & Send" with an "Approve
// only" fallback in the dropdown. Closes on outside-click / Escape.

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { SmoothButton, type SmoothButtonProps } from "./smooth-button";

export interface SplitAction {
  label: string;
  icon?: ReactNode;
  onClick: () => void;
}

export function SplitButton({
  primary,
  actions,
  variant = "success",
  disabled = false,
}: {
  primary: SplitAction;
  actions: SplitAction[];
  variant?: SmoothButtonProps["variant"];
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="relative inline-flex" ref={ref}>
      <div className="inline-flex">
        <SmoothButton
          variant={variant}
          disabled={disabled}
          onClick={primary.onClick}
          className="rounded-r-none"
        >
          {primary.icon}
          {primary.label}
        </SmoothButton>
        <SmoothButton
          variant={variant}
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          aria-label="More actions"
          aria-haspopup="menu"
          aria-expanded={open}
          className="rounded-l-none border-l border-black/25 px-2"
        >
          <ChevronDown className={open ? "rotate-180 transition-transform" : "transition-transform"} />
        </SmoothButton>
      </div>

      {open && actions.length > 0 && (
        <div
          role="menu"
          className="absolute right-0 top-[calc(100%+4px)] z-20 min-w-48 overflow-hidden rounded-lg border shadow-lg"
          style={{ background: "var(--surface)" }}
        >
          {actions.map((a) => (
            <button
              key={a.label}
              role="menuitem"
              disabled={disabled}
              onClick={() => {
                setOpen(false);
                a.onClick();
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-fg transition-colors hover:bg-surface-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:h-4 [&_svg]:w-4 [&_svg]:shrink-0 [&_svg]:text-muted"
            >
              {a.icon}
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
