import * as React from "react";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export function Button({ variant = "primary", className, ...props }: Props) {
  const base = "rounded-xl px-4 py-2 text-sm font-medium border";
  const styles =
    variant === "primary"
      ? "bg-black text-white border-black"
      : "bg-white text-black border-gray-200";
  return <button {...props} className={`${base} ${styles} ${className ?? ""}`} />;
}
