import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { OpenProjectRequest, UpdateModelRequest } from "@/types/api";
import { api } from "./endpoints";

export const queryKeys = {
  health: ["backend", "health"] as const,
  systemStatus: ["system", "status"] as const,
  systemVersion: ["system", "version"] as const,
  models: ["models"] as const,
  activeModel: ["settings", "model"] as const,
  projectInfo: (rootDirectory: string) =>
    ["projects", "info", rootDirectory] as const,
  repositoryIndex: (rootDirectory: string) =>
    ["repository", "index", rootDirectory] as const,
};

export function useBackendHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.health,
  });
}

export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: api.systemStatus,
  });
}

export function useSystemVersion() {
  return useQuery({
    queryKey: queryKeys.systemVersion,
    queryFn: api.systemVersion,
  });
}

export function useModels() {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: api.models,
  });
}

export function useActiveModel() {
  return useQuery({
    queryKey: queryKeys.activeModel,
    queryFn: api.activeModel,
  });
}

export function useUpdateActiveModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: UpdateModelRequest) => api.updateActiveModel(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.activeModel,
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.systemStatus,
      });
    },
  });
}

export function useOpenProject() {
  return useMutation({
    mutationFn: (body: OpenProjectRequest) => api.openProject(body),
  });
}

export function useProjectInfo(rootDirectory: string | null) {
  return useQuery({
    queryKey: queryKeys.projectInfo(rootDirectory ?? ""),
    queryFn: () => api.projectInfo(rootDirectory ?? ""),
    enabled: Boolean(rootDirectory),
  });
}

export function useRepositoryIndex(rootDirectory: string | null) {
  return useQuery({
    queryKey: queryKeys.repositoryIndex(rootDirectory ?? ""),
    queryFn: () => api.repositoryIndex(rootDirectory ?? ""),
    enabled: Boolean(rootDirectory),
  });
}
