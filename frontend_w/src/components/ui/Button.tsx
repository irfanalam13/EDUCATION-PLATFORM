"use client";

import { forwardRef } from "react";

import { cn } from "@/lib/utils";


type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-md px-4 text-sm font-medium transition",
        variant === "primary" && "bg-cyan-700 text-white hover:bg-cyan-800",
        variant === "secondary" && "border border-app bg-card hover:bg-slate-50 dark:hover:bg-slate-800",
        variant === "ghost" && "text-muted hover:text-inherit",
        className,
      )}
      {...props}
    />
  );
});
