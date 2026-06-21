import { cn } from "@/lib/utils";


export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return <section className={cn("rounded-lg border border-app bg-card shadow-panel", className)}>{children}</section>;
}
