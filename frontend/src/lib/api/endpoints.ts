import type {
  ActiveModelResponse,
  HealthResponse,
  ModelsResponse,
  OpenProjectRequest,
  OpenProjectResponse,
  ProjectInfo,
  RepositoryIndex,
  SystemStatus,
  SystemVersion,
  UpdateModelRequest,
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
