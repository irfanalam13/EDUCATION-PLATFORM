import Link from "next/link";

export type Crumb = {
  label: string;
  href?: string; // if missing, it's the current page
};

export default function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="text-sm">
      <ol className="flex flex-wrap items-center gap-2">
        {items.map((c, idx) => {
          const last = idx === items.length - 1;
          return (
            <li key={`${c.label}-${idx}`} className="flex items-center gap-2">
              {c.href && !last ? (
                <Link className="opacity-70 hover:opacity-100 underline" href={c.href}>
                  {c.label}
                </Link>
              ) : (
                <span className={last ? "font-medium" : "opacity-70"}>{c.label}</span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
