import { EmptyState } from "@/components/common/EmptyState";

export function EditingPage() {
  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Editing</h2>
        <p className="text-sm text-muted-foreground">Editing workflow foundation.</p>
      </div>
      <EmptyState
        title="Editing UI is not implemented in Sprint 11"
        description="The shell is ready for plan, review, apply, and rollback workflows."
      />
    </section>
  );
}
