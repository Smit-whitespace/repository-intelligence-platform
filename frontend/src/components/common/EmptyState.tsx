import { Inbox } from "lucide-react";

type EmptyStateProps = {
  title: string;
  description?: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex min-h-32 flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border bg-surface p-6 text-center">
      <Inbox className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
      <h2 className="text-sm font-semibold">{title}</h2>
      {description ? (
        <p className="max-w-lg text-sm text-muted-foreground">{description}</p>
      ) : null}
    </div>
  );
}
