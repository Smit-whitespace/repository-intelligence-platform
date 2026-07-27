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
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Projects</h2>
        <p className="text-sm text-muted-foreground">
          Open a repository-backed project and inspect persisted project metadata.
        </p>
      </div>
      <form
        onSubmit={(event) => {
          void onSubmit(event);
        }}
        className="rounded-md border border-border bg-surface p-4"
      >
        <label className="block text-sm font-medium" htmlFor="rootDirectory">
          Project root directory
        </label>
        <div className="mt-3 flex flex-col gap-3 md:flex-row">
          <input
            id="rootDirectory"
            placeholder="C:/Users/you/projects/my-project"
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
            {...register("rootDirectory")}
          />
          <Button type="submit" disabled={openProject.isPending}>
            {openProject.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <FolderOpen className="mr-2 h-4 w-4" aria-hidden="true" />
            )}
            Open project
          </Button>
        </div>
        {errors.rootDirectory ? (
          <p className="mt-2 text-sm text-red-500">
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
        <section className="rounded-md border border-border bg-surface p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold">Active project</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {activeProject.name}
              </p>
            </div>
            <Button
              className="h-8 bg-muted px-2 text-foreground"
              onClick={() => {
                clearActiveProject();
                toast.info("Active project cleared");
              }}
            >
              <X className="mr-2 h-4 w-4" aria-hidden="true" />
              Clear
            </Button>
          </div>
          {projectInfo.isLoading ? <LoadingState label="Loading project details" /> : null}
          {projectInfo.isError ? <ApiErrorState error={projectInfo.error} /> : null}
          <dl className="mt-4 grid gap-3 text-sm lg:grid-cols-2">
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
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words font-medium">{value}</dd>
    </div>
  );
}
