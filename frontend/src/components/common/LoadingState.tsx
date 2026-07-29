import { cn } from "@/lib/utils/cn";

type LoadingStateProps = {
  label?: string;
  className?: string;
};

export function LoadingState({ label = "Loading", className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-32 flex-col items-center justify-center gap-3",
        className,
      )}
    >
      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#4F8CFF]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#8B5CF6] [animation-delay:150ms]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#4F8CFF] [animation-delay:300ms]" />
      </div>
      <span className="text-sm text-[#7A8599]">{label}</span>
    </div>
  );
}
