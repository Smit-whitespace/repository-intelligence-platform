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

export type ModelSource = "task" | "capability" | "primary" | "embedding";

export type EffectiveModel = {
  operation: string;
  provider: string;
  provider_type: string;
  model: string;
  source: ModelSource;
};

export type EffectiveModelsResponse = {
  models: EffectiveModel[];
};

export type ModelConfigurationView = {
  path: string;
  saved: boolean;
  api_keys_present: Record<string, boolean>;
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

export type ProposalStatus = "pending" | "applied" | "rejected" | "rolled_back";

export type ProposedFile = {
  path: string;
  change: "create" | "modify";
  added_lines: number;
  removed_lines: number;
  diff: string;
};

export type ValidationCommand = {
  name: string;
  argv: string[];
  timeout_seconds?: number;
};

export type ValidationConfig = {
  commands: ValidationCommand[];
};

export type CommandResult = {
  name: string;
  argv: string[];
  passed: boolean;
  exit_code: number | null;
  timed_out: boolean;
  duration_ms: number;
  output: string;
};

export type ValidationReport = {
  ran: boolean;
  passed: boolean;
  results: CommandResult[];
};

export type EditProposal = {
  proposal_id: string;
  created_at: string;
  updated_at: string;
  status: ProposalStatus;
  source: "client" | "planner";
  description: string;
  model: string | null;
  notes: string | null;
  files: ProposedFile[];
  diff: string;
  snapshot_id: string | null;
  validation: ValidationReport | null;
};

export type ProposalListResponse = {
  proposals: EditProposal[];
};

export type PlanEditRequest = {
  repository_root: string;
  instruction: string;
  files: string[];
};
