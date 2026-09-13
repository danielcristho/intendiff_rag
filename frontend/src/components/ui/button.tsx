import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes, ReactNode } from "react";

// ButtonProps is the standard button plus a visual variant and size.
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "solid" | "danger";
  size?: "sm" | "md";
  icon?: ReactNode;
}

// Button renders the shared hairline button used across the app.
export function Button({
  className,
  variant = "default",
  size = "md",
  icon,
  children,
  ...props
}: ButtonProps) {
  const sizes = {
    sm: "px-2.5 py-1.5 text-[0.85rem] gap-1.5",
    md: "px-3.5 py-2 gap-2",
  };

  const variants = {
    default:
      "border-line bg-surface text-ink hover:enabled:bg-accent-soft hover:enabled:border-accent hover:enabled:text-accent",
    solid: "border-accent bg-accent text-white hover:enabled:bg-accent-hover hover:enabled:border-accent-hover",
    danger: "border-danger bg-surface text-danger hover:enabled:bg-danger-soft",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded border font-medium transition-colors duration-100",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        "disabled:cursor-not-allowed disabled:border-hairline disabled:text-ink-faint",
        sizes[size],
        variants[variant],
        className,
      )}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
}
