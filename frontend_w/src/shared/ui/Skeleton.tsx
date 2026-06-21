import React from "react";

export default function Skeleton({
  className = "",
}: {
  className?: string;
}) {
  return <div className={`animate-pulse rounded-lg bg-black/10 ${className}`} />;
}
