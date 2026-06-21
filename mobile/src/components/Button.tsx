import { Pressable, StyleSheet, Text, ViewStyle } from "react-native";

import { palette } from "@/theme";

type ButtonProps = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost";
  style?: ViewStyle;
};

export function Button({ label, onPress, disabled, variant = "primary", style }: ButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        styles[variant],
        pressed && !disabled ? styles.pressed : null,
        disabled ? styles.disabled : null,
        style
      ]}
    >
      <Text style={[styles.text, variant === "primary" ? styles.primaryText : styles.secondaryText]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    alignItems: "center",
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 46,
    justifyContent: "center",
    paddingHorizontal: 16
  },
  primary: {
    backgroundColor: palette.primary,
    borderColor: palette.primary
  },
  secondary: {
    backgroundColor: palette.card,
    borderColor: palette.border
  },
  ghost: {
    backgroundColor: "transparent",
    borderColor: "transparent"
  },
  pressed: {
    opacity: 0.75
  },
  disabled: {
    opacity: 0.45
  },
  text: {
    fontSize: 15,
    fontWeight: "700"
  },
  primaryText: {
    color: "#ffffff"
  },
  secondaryText: {
    color: palette.ink
  }
});
