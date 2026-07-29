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
    <div className="flex min-h-32 flex-col items-center justify-center gap-3 rounded-[var(--radius)] border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.06)] p-8 text-center">
      <div className="rounded-[var(--radius-sm)] bg-[rgba(239,68,68,0.1)] p-2">
        <AlertTriangle className="h-5 w-5 text-[#EF4444]" aria-hidden="true" />
      </div>
      <h2 className="text-sm font-semibold text-[#F8FAFC]">Request failed</h2>
      <p className="max-w-md text-sm leading-relaxed text-[#AAB4C5]">{message}</p>
    </div>
  );
}
