"use client";

// Adapted from 21st.dev "Smooth Button" (educalvolpz), re-themed to our CSS
// variables. Gradient variants + a subtle press-scale for a more tactile feel.

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes, Ref } from "react";
import { cn } from "@/lib/utils";

const smoothButtonVariants = cva(
  "inline-flex cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium text-sm transition-[transform,box-shadow,filter,background-color] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--app)] active:scale-[0.97] active:translate-y-0 motion-reduce:transition-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:h-4 [&_svg]:w-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary:
          "border border-white/15 bg-gradient-to-b from-[var(--accent)] to-[color-mix(in_oklab,var(--accent)_78%,black)] text-[var(--accent-fg)] shadow-md shadow-black/25 hover:-translate-y-px hover:shadow-lg hover:shadow-black/30 hover:brightness-110 [&_svg]:drop-shadow-sm",
        success:
          "border border-white/15 bg-gradient-to-b from-[var(--green)] to-[color-mix(in_oklab,var(--green)_75%,black)] text-white shadow-md shadow-black/25 hover:-translate-y-px hover:shadow-lg hover:shadow-black/30 hover:brightness-110 [&_svg]:drop-shadow-sm",
        danger:
          "border border-white/15 bg-gradient-to-b from-[var(--red)] to-[color-mix(in_oklab,var(--red)_75%,black)] text-white shadow-md shadow-black/25 hover:-translate-y-px hover:shadow-lg hover:shadow-black/30 hover:brightness-110",
        outline:
          "border bg-[var(--surface)] text-[var(--fg)] shadow-sm hover:-translate-y-px hover:bg-[var(--surface-2)] hover:shadow-md",
        ghost: "text-[var(--muted)] hover:bg-[var(--surface-2)] hover:text-[var(--fg)]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3",
        lg: "h-11 rounded-xl px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export type SmoothButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof smoothButtonVariants> & {
    asChild?: boolean;
    ref?: Ref<HTMLButtonElement>;
  };

export function SmoothButton({
  className,
  variant,
  size,
  asChild = false,
  ref,
  ...props
}: SmoothButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp className={cn(smoothButtonVariants({ variant, size, className }))} ref={ref} {...props} />
  );
}

export { smoothButtonVariants };
