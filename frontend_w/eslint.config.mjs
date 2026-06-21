import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "src/shared/**",
    "src/features/academics/**",
    "src/features/accounts/**",
    "src/features/assessment/**",
    "src/features/auth/api/**",
    "src/features/auth/hooks/**",
    "src/features/auth/types/**",
    "src/features/auth/utils/**",
    "src/features/billing/**",
    "src/features/content/api/**",
    "src/features/content/components/**",
    "src/features/content/screens/**",
    "src/features/gamification/**",
    "src/features/mcq/**",
    "src/features/notifications/**",
    "src/features/practice/**",
    "src/features/progress/**",
    "src/features/social/**",
  ]),
]);

export default eslintConfig;
