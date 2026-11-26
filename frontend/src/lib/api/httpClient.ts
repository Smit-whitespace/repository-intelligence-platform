import { config } from "@/lib/config/env";
import { authorizationHeader, useAuthStore } from "@/stores/authStore";
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
      ...authorizationHeader(),
      ...options.headers,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    if (response.status === 401) {
      useAuthStore.getState().markRejected();
    }

    throw await toApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
