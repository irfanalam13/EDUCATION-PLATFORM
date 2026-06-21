import { StyleSheet, TextInput, TextInputProps, View } from "react-native";

import { palette, spacing } from "@/theme";
import { Text } from "./Text";

type FieldProps = TextInputProps & {
  label: string;
  hint?: string;
};

export function Field({ label, hint, style, ...props }: FieldProps) {
  return (
    <View style={styles.wrapper}>
      <Text variant="label">{label}</Text>
      {hint ? <Text variant="muted">{hint}</Text> : null}
      <TextInput
        placeholderTextColor="#94a3b8"
        {...props}
        style={[styles.input, props.multiline ? styles.multiline : null, style]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: spacing.xs
  },
  input: {
    backgroundColor: palette.card,
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    color: palette.ink,
    fontSize: 15,
    minHeight: 46,
    paddingHorizontal: 12
  },
  multiline: {
    minHeight: 110,
    paddingTop: 12,
    textAlignVertical: "top"
  }
});
