import { config } from "@/lib/config/env";
import { toApiError } from "./errors";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

function buildUrl(path: string) {
  return `${config.apiBaseUrl}${path}`;
}

export async function request<T>(path: string, options: RequestOptions = {}) {
  const response = await fetch(buildUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
