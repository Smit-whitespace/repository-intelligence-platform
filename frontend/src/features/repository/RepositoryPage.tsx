import { EmptyState } from "@/components/common/EmptyState";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { useRepositoryIndex } from "@/lib/api/queries";
import { formatBytes, formatDate } from "@/lib/utils/format";
import { useProjectStore } from "@/stores/projectStore";
import type { RepositoryEntry } from "@/types/api";
import type { ReactNode } from "react";

export function RepositoryPage() {
  const activeProject = useProjectStore((state) => state.activeProject);
  const repository = useRepositoryIndex(activeProject?.root_directory ?? null);
  const entries = repository.data?.entries ?? [];
  const files = entries.filter((entry) => !entry.is_directory);
  const textFiles = files.filter((entry) => entry.is_text_file);
  const languages = languageStats(files);
  const largestFiles = [...files]
    .sort((left, right) => (right.size_bytes ?? 0) - (left.size_bytes ?? 0))
    .slice(0, 8);
  const recentFiles = [...files]
    .filter((entry) => entry.modified_at)
    .sort((left, right) =>
      String(right.modified_at).localeCompare(String(left.modified_at)),
    )
    .slice(0, 8);

  if (!activeProject) {
    return (
      <section className="animate-fade-in space-y-8">
        <div>
          <h1 className="text-lg font-semibold text-[#F8FAFC]">Search</h1>
          <p className="mt-1 text-sm text-[#7A8599]">
            Repository overview and indexing state.
          </p>
        </div>
        <EmptyState
          title="No project open"
          description="Open a project before inspecting repository metadata."
        />
      </section>
    );
  }

  return (
    <section className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-[#F8FAFC]">Search</h1>
        <p className="mt-1 font-mono text-xs text-[#7A8599]">
          {activeProject.root_directory}
        </p>
      </div>
      {repository.isLoading ? <LoadingState label="Scanning repository" /> : null}
      {repository.isError ? <ApiErrorState error={repository.error} /> : null}
      {repository.data ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric
              label="Files"
              value={repository.data.summary.files.toLocaleString()}
            />
            <Metric
              label="Directories"
              value={repository.data.summary.directories.toLocaleString()}
            />
            <Metric
              label="Size"
              value={formatBytes(repository.data.summary.total_size_bytes)}
            />
            <Metric label="Text files" value={textFiles.length.toLocaleString()} />
          </div>
          <div className="grid gap-4 xl:grid-cols-3">
            <Panel title="Supported languages">
              {languages.length ? (
                <div className="space-y-3">
                  {languages.map((language) => (
                    <div
                      key={language.name}
                      className="flex items-center justify-between gap-3 text-sm"
                    >
                      <span className="text-[#AAB4C5]">{language.name}</span>
                      <span className="text-xs text-[#7A8599]">
                        {language.count}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#7A8599]">
                  No language metadata reported.
                </p>
              )}
            </Panel>
            <Panel title="Largest files">
              <FileList entries={largestFiles} mode="size" />
            </Panel>
            <Panel title="Recently modified">
              <FileList entries={recentFiles} mode="modified" />
            </Panel>
          </div>
          <Panel title="Repository metadata">
            <dl className="grid gap-4 text-sm md:grid-cols-2">
              <Detail label="Project" value={activeProject.name} />
              <Detail label="Root" value={activeProject.root_directory} />
              <Detail label="Entries" value={entries.length.toLocaleString()} />
              <Detail label="Indexing state" value="available" />
            </dl>
          </Panel>
        </>
      ) : null}
    </section>
  );
}

type MetricProps = {
  label: string;
  value: string;
};

function Metric({ label, value }: MetricProps) {
  return (
    <div className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-[#7A8599]">
        {label}
      </p>
      <p className="mt-2 text-sm font-semibold text-[#F8FAFC]">{value}</p>
    </div>
  );
}

type PanelProps = {
  title: string;
  children: ReactNode;
};

function Panel({ title, children }: PanelProps) {
  return (
    <section className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
      <h3 className="text-sm font-semibold text-[#F8FAFC]">{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}

type FileListProps = {
  entries: RepositoryEntry[];
  mode: "size" | "modified";
};

function FileList({ entries, mode }: FileListProps) {
  if (!entries.length) {
    return <p className="text-sm text-[#7A8599]">No files reported.</p>;
  }

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div key={entry.relative_path} className="min-w-0 text-sm">
          <p
            className="truncate font-mono text-xs text-[#AAB4C5]"
            title={entry.relative_path}
          >
            {entry.relative_path}
          </p>
          <p className="mt-0.5 text-xs text-[#7A8599]">
            {mode === "size"
              ? formatBytes(entry.size_bytes ?? 0)
              : formatDate(entry.modified_at)}
          </p>
        </div>
      ))}
    </div>
  );
}

type DetailProps = {
  label: string;
  value: string;
};

function Detail({ label, value }: DetailProps) {
  return (
    <div>
      <dt className="text-xs font-medium text-[#7A8599]">{label}</dt>
      <dd className="mt-1 break-words font-mono text-xs text-[#AAB4C5]">{value}</dd>
    </div>
  );
}

function languageStats(entries: RepositoryEntry[]) {
  const counts = new Map<string, number>();

  for (const entry of entries) {
    if (entry.language) {
      counts.set(entry.language, (counts.get(entry.language) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .map(([name, count]) => ({
      name,
      count,
    }))
    .sort((left, right) => right.count - left.count)
    .slice(0, 10);
}
