import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({ className, type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex h-9 items-center justify-center rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground transition hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary disabled:pointer-events-none disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
