import { Loader2 } from "lucide-react";

type LoadingStateProps = {
  label?: string;
};

export function LoadingState({ label = "Loading" }: LoadingStateProps) {
  return (
    <div className="flex min-h-32 items-center justify-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
