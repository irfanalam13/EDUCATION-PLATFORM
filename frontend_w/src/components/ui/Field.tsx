import { cn } from "@/lib/utils";


export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-2">
      <div>
        <div className="text-sm font-medium">{label}</div>
        {hint ? <div className="text-xs text-muted">{hint}</div> : null}
      </div>
      {children}
    </label>
  );
}


export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        "h-11 w-full rounded-md border border-app bg-transparent px-3 text-sm outline-none transition focus:border-cyan-600",
        props.className,
      )}
    />
  );
}


export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={cn(
        "min-h-[120px] w-full rounded-md border border-app bg-transparent px-3 py-2 text-sm outline-none transition focus:border-cyan-600",
        props.className,
      )}
    />
  );
}
