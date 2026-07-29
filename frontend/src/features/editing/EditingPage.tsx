import { EmptyState } from "@/components/common/EmptyState";

export function EditingPage() {
  return (
    <section className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-[#F8FAFC]">Editing</h1>
        <p className="mt-1 text-sm text-[#7A8599]">
          Plan, review, and apply code changes.
        </p>
      </div>
      <EmptyState
        title="Editing — Available Soon"
        description="The shell is ready for plan, review, apply, and rollback workflows."
      />
    </section>
  );
}
