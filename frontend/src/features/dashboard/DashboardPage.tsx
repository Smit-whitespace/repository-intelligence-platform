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
    <section className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-[#F8FAFC]">Dashboard</h1>
        <p className="mt-1 text-sm text-[#7A8599]">
          Workspace status and overview.
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
        <Panel title="Project">
          <dl className="space-y-4 text-sm">
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
        </Panel>
        <Panel title="Repository summary">
          <dl className="space-y-4 text-sm">
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
        </Panel>
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
    <div className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-[#7A8599]">
        {label}
      </p>
      <p
        className={
          tone === "ok"
            ? "mt-2 text-sm font-semibold text-[#10B981]"
            : "mt-2 text-sm font-semibold text-[#F8FAFC]"
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
    <div className="flex items-start justify-between gap-4">
      <dt className="shrink-0 text-[#7A8599]">{label}</dt>
      <dd className="min-w-0 truncate text-right font-medium text-[#F8FAFC]" title={value}>
        {value}
      </dd>
    </div>
  );
}

type PanelProps = {
  title: string;
  children: React.ReactNode;
};

function Panel({ title, children }: PanelProps) {
  return (
    <section className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
      <h3 className="text-sm font-semibold text-[#F8FAFC]">{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}
