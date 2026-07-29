import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

export function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex h-9 items-center justify-center gap-2 rounded-[var(--radius-sm)] px-4 text-sm font-medium transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-40",
        variant === "primary" &&
          "bg-gradient-to-r from-[#4F8CFF] to-[#8B5CF6] text-white hover:opacity-90 active:opacity-80",
        variant === "secondary" &&
          "border border-[rgba(255,255,255,0.12)] bg-transparent text-[#AAB4C5] hover:border-[rgba(255,255,255,0.2)] hover:text-[#F8FAFC] active:bg-[rgba(255,255,255,0.04)]",
        variant === "ghost" &&
          "bg-transparent text-[#AAB4C5] hover:text-[#F8FAFC] hover:bg-[rgba(255,255,255,0.04)] active:bg-[rgba(255,255,255,0.08)]",
        className,
      )}
      {...props}
    />
  );
}
