export type HealthResponse = {
  status: string;
  application: string;
  version: string;
};

export type SystemStatus = {
  backend_health: string;
  provider_connectivity: string;
  active_provider: string;
  active_model: string;
  project_status: string;
  repository_status: string;
  indexing_state: string;
};

export type SystemVersion = {
  application_name: string;
  application_version: string;
  api_version: string;
  backend_version: string;
};

export type ModelInfo = {
  provider: string;
  name: string;
};

export type ModelsResponse = {
  models: ModelInfo[];
};

export type ActiveModelResponse = {
  active_provider: string;
  active_model: string;
};

export type UpdateModelRequest = {
  model: string;
};

export type OpenProjectRequest = {
  root_directory: string;
};

export type OpenProjectResponse = {
  project: string;
  root_directory: string;
};

export type ProjectInfo = {
  name: string;
  root_directory: string;
  storage_directory: string;
  created_at: string;
};

export type RepositorySummary = {
  files: number;
  directories: number;
  total_size_bytes: number;
};

export type RepositoryEntry = {
  name: string;
  relative_path: string;
  is_directory: boolean;
  size_bytes: number | null;
  modified_at: string | null;
  language: string | null;
  sha256: string | null;
  is_text_file: boolean | null;
  mime_type: string | null;
};

export type RepositoryIndex = {
  summary: RepositorySummary;
  entries: RepositoryEntry[];
};
