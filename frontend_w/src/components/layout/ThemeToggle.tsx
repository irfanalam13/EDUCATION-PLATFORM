"use client";

import { useEffect, useState } from "react";

import { Button } from "../ui/Button";


export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const saved = window.localStorage.getItem("edu-theme");
    if (saved === "dark" || saved === "light") {
      return saved;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("edu-theme", theme);
  }, [theme]);

  return (
    <Button
      variant="secondary"
      onClick={() => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        document.documentElement.classList.toggle("dark", next === "dark");
        window.localStorage.setItem("edu-theme", next);
      }}
    >
      {theme === "dark" ? "Light" : "Dark"}
    </Button>
  );
}
