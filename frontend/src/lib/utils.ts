import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// cn merges Tailwind class names, letting later classes win over earlier ones.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// formatPct renders a 0-1 ratio as a percentage, or an em dash when unknown.
export function formatPct(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}
