"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Home", href: "/" },
  { label: "Academics", href: "/academics" },
  { label: "Levels", href: "/academics/levels" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const panelRef = React.useRef<HTMLDivElement | null>(null);

  // Close menu on route change
  React.useEffect(() => setOpen(false), [pathname]);

  // Close on outside click
  React.useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!open) return;
      const target = e.target as Node;
      if (panelRef.current && !panelRef.current.contains(target)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  return (
    <header className="sticky top-0 z-50 border-b bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-xl border flex items-center justify-center font-bold">
              E
            </div>
            <div className="leading-tight">
              <div className="font-semibold">Edu Platform</div>
              <div className="text-xs opacity-60">Academics</div>
            </div>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-2">
            {navItems.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`text-sm rounded-lg px-3 py-2 transition ${
                    active ? "bg-black text-white" : "opacity-80 hover:opacity-100 hover:bg-black/5"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <Link
              href="/academics/levels"
              className="hidden md:inline-flex rounded-lg border px-4 py-2 text-sm hover:bg-black/5"
            >
              Browse curriculum
            </Link>

            {/* Mobile menu button */}
            <button
              className="inline-flex md:hidden rounded-lg border px-3 py-2"
              onClick={() => setOpen((v) => !v)}
              aria-label="Toggle menu"
              aria-expanded={open}
            >
              <span className="block h-4 w-5 relative">
                <span className="absolute left-0 top-0 h-0.5 w-5 bg-black" />
                <span className="absolute left-0 top-1.5 h-0.5 w-5 bg-black" />
                <span className="absolute left-0 top-3 h-0.5 w-5 bg-black" />
              </span>
            </button>
          </div>
        </div>

        {/* Mobile nav dropdown */}
        {open ? (
          <div ref={panelRef} className="md:hidden mt-3 rounded-xl border bg-white p-2">
            <nav className="flex flex-col">
              {navItems.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-lg px-3 py-2 text-sm transition ${
                      active ? "bg-black text-white" : "hover:bg-black/5"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}

            </nav>
          </div>
        ) : null}
      </div>
    </header>
  );
}
