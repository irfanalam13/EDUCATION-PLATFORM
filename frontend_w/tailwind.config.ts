import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        border: "#e5e7eb",
        surface: "#ffffff",
        muted: "#6b7280",
        ink: "#111827",
        brand: {
          50: "#ecfeff",
          100: "#cffafe",
          500: "#0891b2",
          600: "#0e7490",
          700: "#155e75",
        },
      },
      boxShadow: {
        panel: "0 10px 30px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
