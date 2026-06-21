import * as React from "react";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full rounded-xl border px-3 py-2 outline-none focus:ring ${
        props.className ?? ""
      }`}
    />
  );
}
