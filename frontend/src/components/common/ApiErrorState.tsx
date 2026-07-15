import { AlertTriangle } from "lucide-react";
import { ApiError } from "@/lib/api/errors";

type ApiErrorStateProps = {
  error: unknown;
};

export function ApiErrorState({ error }: ApiErrorStateProps) {
  const message =
    error instanceof ApiError
      ? error.message
      : "The backend request could not be completed.";

  return (
    <div className="flex min-h-32 flex-col items-center justify-center gap-2 rounded-md border border-border bg-surface p-6 text-center">
      <AlertTriangle className="h-5 w-5 text-red-500" aria-hidden="true" />
      <h2 className="text-sm font-semibold">Request failed</h2>
      <p className="max-w-lg text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
