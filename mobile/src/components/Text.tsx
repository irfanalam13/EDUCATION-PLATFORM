import { StyleSheet, Text as RNText, TextProps } from "react-native";

import { palette } from "@/theme";

type AppTextProps = TextProps & {
  variant?: "title" | "subtitle" | "body" | "label" | "muted";
};

export function Text({ variant = "body", style, ...props }: AppTextProps) {
  return <RNText {...props} style={[styles.base, styles[variant], style]} />;
}

const styles = StyleSheet.create({
  base: {
    color: palette.ink
  },
  title: {
    fontSize: 28,
    lineHeight: 34,
    fontWeight: "800"
  },
  subtitle: {
    fontSize: 20,
    lineHeight: 26,
    fontWeight: "700"
  },
  body: {
    fontSize: 15,
    lineHeight: 22
  },
  label: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "700"
  },
  muted: {
    color: palette.muted,
    fontSize: 14,
    lineHeight: 20
  }
});
