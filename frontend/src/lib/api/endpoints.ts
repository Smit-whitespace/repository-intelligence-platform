import type {
  ActiveModelResponse,
  EditProposal,
  EffectiveModelsResponse,
  HealthResponse,
  ModelConfigurationView,
  ModelsResponse,
  OpenProjectRequest,
  OpenProjectResponse,
  PlanEditRequest,
  ProjectInfo,
  ProposalListResponse,
  RepositoryIndex,
  SystemStatus,
  SystemVersion,
  UpdateModelRequest,
  ValidationConfig,
  ValidationReport,
} from "@/types/api";
import { request } from "./httpClient";

function pathWithQuery(path: string, params: Record<string, string>) {
  return `${path}?${new URLSearchParams(params).toString()}`;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  systemStatus: () => request<SystemStatus>("/system/status"),
  systemVersion: () => request<SystemVersion>("/system/version"),
  models: () => request<ModelsResponse>("/models"),
  activeModel: () => request<ActiveModelResponse>("/settings/model"),
  effectiveModels: () => request<EffectiveModelsResponse>("/models/effective"),
  modelConfiguration: () =>
    request<ModelConfigurationView>("/models/configuration"),
  proposals: (rootDirectory: string) =>
    request<ProposalListResponse>(
      pathWithQuery("/editing/proposals", { root_directory: rootDirectory }),
    ),
  planProposal: (body: PlanEditRequest) =>
    request<EditProposal>("/editing/proposals/plan", {
      method: "POST",
      body,
    }),
  proposalAction: (
    rootDirectory: string,
    proposalId: string,
    action: "apply" | "reject" | "rollback",
    validateAfter = true,
  ) =>
    request<EditProposal>(`/editing/proposals/${proposalId}/${action}`, {
      method: "POST",
      body: {
        repository_root: rootDirectory,
        ...(action === "apply" ? { validate_after: validateAfter } : {}),
      },
    }),
  validationConfig: (rootDirectory: string) =>
    request<ValidationConfig>(
      pathWithQuery("/editing/validation", { root_directory: rootDirectory }),
    ),
  saveValidationConfig: (rootDirectory: string, config: ValidationConfig) =>
    request<ValidationConfig>("/editing/validation", {
      method: "PUT",
      body: { repository_root: rootDirectory, config },
    }),
  runValidation: (rootDirectory: string) =>
    request<ValidationReport>("/editing/validation/run", {
      method: "POST",
      body: { repository_root: rootDirectory },
    }),
  updateActiveModel: (body: UpdateModelRequest) =>
    request<ActiveModelResponse>("/settings/model", {
      method: "PUT",
      body,
    }),
  openProject: (body: OpenProjectRequest) =>
    request<OpenProjectResponse>("/projects/open", {
      method: "POST",
      body,
    }),
  projectInfo: (rootDirectory: string) =>
    request<ProjectInfo>(
      pathWithQuery("/projects/info", {
        root_directory: rootDirectory,
      }),
    ),
  repositoryIndex: (rootDirectory: string) =>
    request<RepositoryIndex>(
      pathWithQuery("/repository/index", {
        root_directory: rootDirectory,
      }),
    ),
};
