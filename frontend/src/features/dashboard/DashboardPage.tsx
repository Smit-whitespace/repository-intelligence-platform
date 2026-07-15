import { ApiErrorState } from "@/components/common/ApiErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import {
  useActiveModel,
  useBackendHealth,
  useModels,
  useRepositoryIndex,
  useSystemStatus,
  useSystemVersion,
} from "@/lib/api/queries";
import { formatBytes } from "@/lib/utils/format";
import { useProjectStore } from "@/stores/projectStore";

export function DashboardPage() {
  const health = useBackendHealth();
  const status = useSystemStatus();
  const version = useSystemVersion();
  const activeModel = useActiveModel();
  const models = useModels();
  const activeProject = useProjectStore((state) => state.activeProject);
  const repository = useRepositoryIndex(activeProject?.root_directory ?? null);

  if (health.isLoading || status.isLoading || version.isLoading) {
    return <LoadingState label="Loading dashboard" />;
  }

  if (health.isError) {
    return <ApiErrorState error={health.error} />;
  }

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Repository Intelligence Platform (RIP) workspace status.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="Backend" value={health.data?.status ?? "unknown"} tone="ok" />
        <Metric
          label="Provider"
          value={status.data?.provider_connectivity ?? "unknown"}
        />
        <Metric
          label="Active model"
          value={activeModel.data?.active_model ?? status.data?.active_model ?? "none"}
        />
        <Metric
          label="Version"
          value={version.data?.application_version ?? "unknown"}
        />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-border bg-surface p-4">
          <h3 className="text-sm font-semibold">Project</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <Row label="Name" value={activeProject?.name ?? "No project open"} />
            <Row
              label="Repository"
              value={activeProject?.root_directory ?? "Open a project to begin"}
            />
            <Row
              label="Repository status"
              value={
                repository.isLoading
                  ? "scanning"
                  : repository.data
                    ? "indexed"
                    : status.data?.repository_status ?? "not_loaded"
              }
            />
            <Row
              label="Indexing"
              value={repository.data ? "available" : status.data?.indexing_state ?? "unknown"}
            />
          </dl>
        </section>
        <section className="rounded-md border border-border bg-surface p-4">
          <h3 className="text-sm font-semibold">Repository summary</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <Row
              label="Files"
              value={repository.data?.summary.files.toLocaleString() ?? "none"}
            />
            <Row
              label="Directories"
              value={repository.data?.summary.directories.toLocaleString() ?? "none"}
            />
            <Row
              label="Size"
              value={
                repository.data
                  ? formatBytes(repository.data.summary.total_size_bytes)
                  : "none"
              }
            />
            <Row
              label="Installed models"
              value={
                models.data?.models.length
                  ? models.data.models.map((model) => model.name).join(", ")
                  : "No models reported"
              }
            />
          </dl>
        </section>
      </div>
    </section>
  );
}

type MetricProps = {
  label: string;
  value: string;
  tone?: "ok" | "default";
};

function Metric({ label, value, tone = "default" }: MetricProps) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p
        className={
          tone === "ok"
            ? "mt-2 text-sm font-semibold text-primary"
            : "mt-2 text-sm font-semibold"
        }
      >
        {value}
      </p>
    </div>
  );
}

type RowProps = {
  label: string;
  value: string;
};

function Row({ label, value }: RowProps) {
  return (
    <div className="grid gap-2 sm:grid-cols-[8rem_1fr]">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="min-w-0 truncate font-medium" title={value}>
        {value}
      </dd>
    </div>
  );
}
