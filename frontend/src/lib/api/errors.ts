export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function toApiError(response: Response): Promise<ApiError> {
  const fallback = `Request failed with status ${response.status}`;

  try {
    const payload = (await response.json()) as { detail?: unknown };

    if (typeof payload.detail === "string") {
      return new ApiError(payload.detail, response.status);
    }
  } catch {
    return new ApiError(fallback, response.status);
  }

  return new ApiError(fallback, response.status);
}
