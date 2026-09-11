import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-xl bg-surface p-6 shadow-card", className)} {...props} />;
}

/** Blok status pinggir putus-putus untuk kondisi loading / kosong / error. */
export function StateBlock({
  tone = "muted",
  children,
}: {
  tone?: "muted" | "error";
  children: ReactNodeLike;
}) {
  return (
    <p
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "m-0 rounded border p-4",
        tone === "error" ? "border-solid border-danger text-danger" : "border-dashed border-hairline text-ink-faint",
      )}
    >
      {children}
    </p>
  );
}

type ReactNodeLike = HTMLAttributes<HTMLDivElement>["children"];
