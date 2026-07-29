import { cn } from "@/lib/utils/cn";

type EmptyStateProps = {
  title: string;
  description?: string;
  className?: string;
};

export function EmptyState({ title, description, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-32 flex-col items-center justify-center gap-3 rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-8 text-center",
        className,
      )}
    >
      <div className="rounded-[var(--radius-sm)] bg-[#1A2335] p-3">
        <img src="/logo.png" alt="" className="h-8 w-8 opacity-40" />
      </div>
      <h2 className="text-sm font-semibold text-[#F8FAFC]">{title}</h2>
      {description ? (
        <p className="max-w-md text-sm leading-relaxed text-[#7A8599]">
          {description}
        </p>
      ) : null}
    </div>
  );
}
