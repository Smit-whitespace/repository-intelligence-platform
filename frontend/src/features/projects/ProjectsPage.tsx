import { zodResolver } from "@hookform/resolvers/zod";
import { FolderOpen, RefreshCw, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api/endpoints";
import { queryKeys, useOpenProject, useProjectInfo } from "@/lib/api/queries";
import { queryClient } from "@/lib/api/queryClient";
import { formatDate } from "@/lib/utils/format";
import { useProjectStore } from "@/stores/projectStore";

const projectSchema = z.object({
  rootDirectory: z.string().min(1, "Project root is required."),
});

type ProjectForm = z.infer<typeof projectSchema>;

export function ProjectsPage() {
  const activeProject = useProjectStore((state) => state.activeProject);
  const setActiveProject = useProjectStore((state) => state.setActiveProject);
  const clearActiveProject = useProjectStore((state) => state.clearActiveProject);
  const openProject = useOpenProject();
  const projectInfo = useProjectInfo(activeProject?.root_directory ?? null);
  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<ProjectForm>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      rootDirectory: activeProject?.root_directory ?? "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    const opened = await openProject.mutateAsync({
      root_directory: values.rootDirectory,
    });
    const project = await api.projectInfo(opened.root_directory);

    setActiveProject(project);
    queryClient.setQueryData(queryKeys.projectInfo(project.root_directory), project);
    void queryClient.invalidateQueries({
      queryKey: queryKeys.repositoryIndex(project.root_directory),
    });
    toast.success("Project opened");
  });

  return (
    <section className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-[#F8FAFC]">Repository</h1>
        <p className="mt-1 text-sm text-[#7A8599]">
          Open a project directory to enable repository-aware features.
        </p>
      </div>
      <form
        onSubmit={(event) => {
          void onSubmit(event);
        }}
        className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5"
      >
        <label
          className="block text-sm font-medium text-[#F8FAFC]"
          htmlFor="rootDirectory"
        >
          Project root directory
        </label>
        <div className="mt-3 flex flex-col gap-3 md:flex-row">
          <input
            id="rootDirectory"
            placeholder="/home/user/projects/my-project"
            className="h-10 min-w-0 flex-1 rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.1)] bg-[#0A0F1E] px-3 text-sm text-[#F8FAFC] placeholder-[#7A8599] outline-none transition focus:border-[#4F8CFF]/50"
            {...register("rootDirectory")}
          />
          <Button type="submit" disabled={openProject.isPending}>
            {openProject.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <FolderOpen className="h-4 w-4" aria-hidden="true" />
            )}
            Open project
          </Button>
        </div>
        {errors.rootDirectory ? (
          <p className="mt-2 text-sm text-[#EF4444]">
            {errors.rootDirectory.message}
          </p>
        ) : null}
        {openProject.isError ? (
          <div className="mt-4">
            <ApiErrorState error={openProject.error} />
          </div>
        ) : null}
      </form>
      {activeProject ? (
        <section className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-[#F8FAFC]">
                Active project
              </h3>
              <p className="mt-1 text-sm text-[#AAB4C5]">
                {activeProject.name}
              </p>
            </div>
            <Button
              variant="secondary"
              className="h-8 px-3"
              onClick={() => {
                clearActiveProject();
                toast.info("Active project cleared");
              }}
            >
              <X className="h-3.5 w-3.5" />
              Clear
            </Button>
          </div>
          {projectInfo.isLoading ? <LoadingState label="Loading project details" /> : null}
          {projectInfo.isError ? <ApiErrorState error={projectInfo.error} /> : null}
          <dl className="mt-4 grid gap-4 text-sm lg:grid-cols-2">
            <Detail label="Name" value={projectInfo.data?.name ?? activeProject.name} />
            <Detail label="Root" value={activeProject.root_directory} />
            <Detail
              label="Storage"
              value={projectInfo.data?.storage_directory ?? activeProject.storage_directory}
            />
            <Detail
              label="Created"
              value={formatDate(projectInfo.data?.created_at ?? activeProject.created_at)}
            />
          </dl>
        </section>
      ) : (
        <EmptyState
          title="No project open"
          description="Enter a repository root directory to open or initialize its RIP project metadata."
        />
      )}
    </section>
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
