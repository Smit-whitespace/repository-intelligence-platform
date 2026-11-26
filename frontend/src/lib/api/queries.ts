import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  OpenProjectRequest,
  PlanEditRequest,
  UpdateModelRequest,
  ValidationConfig,
} from "@/types/api";
import { api } from "./endpoints";

export const queryKeys = {
  health: ["backend", "health"] as const,
  systemStatus: ["system", "status"] as const,
  systemVersion: ["system", "version"] as const,
  models: ["models"] as const,
  activeModel: ["settings", "model"] as const,
  effectiveModels: ["models", "effective"] as const,
  modelConfiguration: ["models", "configuration"] as const,
  proposals: (rootDirectory: string) =>
    ["editing", "proposals", rootDirectory] as const,
  validationConfig: (rootDirectory: string) =>
    ["editing", "validation", rootDirectory] as const,
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

export function useSystemStatus(options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: api.systemStatus,
    enabled: options.enabled ?? true,
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

export function useEffectiveModels() {
  return useQuery({
    queryKey: queryKeys.effectiveModels,
    queryFn: api.effectiveModels,
  });
}

export function useModelConfiguration() {
  return useQuery({
    queryKey: queryKeys.modelConfiguration,
    queryFn: api.modelConfiguration,
  });
}

export function useProposals(rootDirectory: string | null) {
  return useQuery({
    queryKey: queryKeys.proposals(rootDirectory ?? ""),
    queryFn: () => api.proposals(rootDirectory ?? ""),
    enabled: Boolean(rootDirectory),
  });
}

export function usePlanProposal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: PlanEditRequest) => api.planProposal(body),
    onSuccess: (_proposal, body) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.proposals(body.repository_root),
      });
    },
  });
}

export function useProposalAction(rootDirectory: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      proposalId,
      action,
      validateAfter,
    }: {
      proposalId: string;
      action: "apply" | "reject" | "rollback";
      validateAfter?: boolean;
    }) => api.proposalAction(rootDirectory, proposalId, action, validateAfter),
    onSettled: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.proposals(rootDirectory),
      });
    },
  });
}

export function useValidationConfig(rootDirectory: string | null) {
  return useQuery({
    queryKey: queryKeys.validationConfig(rootDirectory ?? ""),
    queryFn: () => api.validationConfig(rootDirectory ?? ""),
    enabled: Boolean(rootDirectory),
  });
}

export function useSaveValidationConfig(rootDirectory: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: ValidationConfig) =>
      api.saveValidationConfig(rootDirectory, config),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.validationConfig(rootDirectory),
      });
    },
  });
}

export function useRunValidation(rootDirectory: string) {
  return useMutation({
    mutationFn: () => api.runValidation(rootDirectory),
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
      void queryClient.invalidateQueries({
        queryKey: queryKeys.effectiveModels,
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.modelConfiguration,
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
