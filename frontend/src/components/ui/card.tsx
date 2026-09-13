import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

// Card is the standard raised panel every page is built from.
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-xl bg-surface p-6 shadow-card", className)} {...props} />;
}
