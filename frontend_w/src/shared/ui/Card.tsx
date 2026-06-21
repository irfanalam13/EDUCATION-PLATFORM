import React from "react";

export default function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border bg-white/50 p-4 shadow-sm">{children}</div>;
}
