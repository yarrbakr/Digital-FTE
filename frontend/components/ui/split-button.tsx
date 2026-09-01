"use client";

// A split action button: a primary action on the left + a chevron that opens a
// small menu of secondary actions. Used for "Approve & Send" with an "Approve
// only" fallback in the dropdown. The two segments read as one elevated control
// (shared shadow, hairline divider); the menu fades + scales in from its top-
// right corner and closes on outside-click / Escape.

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
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

  // The joined control glows as one unit in its own semantic color.
  const glow =
    variant === "success"
      ? "var(--green)"
      : variant === "danger"
        ? "var(--red)"
        : "var(--accent)";

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
      {/* One elevated control: a shared colored glow on the wrapper, seamless
          segments (each segment stays flat and cancels its own glow/lift). */}
      <div
        className="inline-flex rounded-lg transition-[transform,box-shadow] duration-200 ease-out shadow-[0_4px_16px_-4px_color-mix(in_oklab,var(--glow-color)_50%,transparent)] hover:-translate-y-px hover:shadow-[0_12px_36px_-8px_color-mix(in_oklab,var(--glow-color)_68%,transparent)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
        style={{ ["--glow-color" as string]: glow }}
      >
        <SmoothButton
          variant={variant}
          disabled={disabled}
          onClick={primary.onClick}
          className="rounded-r-none shadow-none hover:translate-y-0 hover:shadow-none"
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
          className="rounded-l-none px-2 shadow-none hover:translate-y-0 hover:shadow-none before:absolute before:left-0 before:top-1/2 before:z-20 before:h-5 before:w-px before:-translate-y-1/2 before:bg-white/25 before:content-['']"
        >
          <ChevronDown
            className={cn(
              "transition-transform duration-300 ease-out",
              open && "rotate-180",
            )}
          />
        </SmoothButton>
      </div>

      {actions.length > 0 && (
        <div
          role="menu"
          aria-hidden={!open}
          className={cn(
            "absolute right-0 bottom-[calc(100%+8px)] z-30 min-w-[16rem] origin-bottom-right overflow-hidden rounded-xl border p-1 shadow-xl shadow-black/40 backdrop-blur-md transition-all duration-200 ease-out motion-reduce:transition-none",
            open
              ? "pointer-events-auto translate-y-0 scale-100 opacity-100"
              : "pointer-events-none translate-y-1 scale-95 opacity-0",
          )}
          style={{ background: "color-mix(in oklab, var(--surface) 90%, transparent)" }}
        >
          {actions.map((a) => (
            <button
              key={a.label}
              role="menuitem"
              tabIndex={open ? 0 : -1}
              disabled={disabled}
              onClick={() => {
                setOpen(false);
                a.onClick();
              }}
              className="group flex w-full items-center gap-3 whitespace-nowrap rounded-lg px-2.5 py-2 text-left text-sm font-medium text-fg transition-colors hover:bg-surface-2 disabled:pointer-events-none disabled:opacity-50"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-surface-2 text-muted transition-colors duration-150 group-hover:bg-[var(--accent-soft)] group-hover:text-[var(--accent)] [&_svg]:h-4 [&_svg]:w-4">
                {a.icon}
              </span>
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
