import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

// StateBlock is the dashed placeholder shown while loading, empty, or failed.
export function StateBlock({
  tone = "muted",
  children,
}: {
  tone?: "muted" | "error";
  children: ReactNode;
}) {
  return (
    <p
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "m-0 rounded border p-4",
        tone === "error"
          ? "border-solid border-danger text-danger"
          : "border-dashed border-hairline text-ink-faint",
      )}
    >
      {children}
    </p>
  );
}
