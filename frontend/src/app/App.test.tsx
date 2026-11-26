import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { queryClient } from "@/lib/api/queryClient";
import { captureTokenFromUrl, useAuthStore } from "@/stores/authStore";
import { App } from "./App";

const responses: Record<string, unknown> = {
  "/api/v1/health": {
    status: "healthy",
    application: "Repository Intelligence Platform (RIP)",
    version: "0.1.0",
  },
  "/api/v1/system/status": {
    backend_health: "healthy",
    provider_connectivity: "available",
    active_provider: "ollama",
    active_model: "qwen3.6",
    project_status: "not_loaded",
    repository_status: "not_loaded",
    indexing_state: "available",
  },
  "/api/v1/system/version": {
    application_name: "Repository Intelligence Platform (RIP)",
    application_version: "0.1.0",
    api_version: "v1",
    backend_version: "0.1.0",
  },
  "/api/v1/models": {
    models: [{ provider: "ollama", name: "qwen3.6" }],
  },
  "/api/v1/settings/model": {
    active_provider: "ollama",
    active_model: "qwen3.6",
  },
  "/api/v1/models/effective": {
    models: [
      {
        operation: "chat",
        provider: "ollama",
        provider_type: "ollama",
        model: "qwen3.6",
        source: "primary",
      },
      {
        operation: "embedding",
        provider: "ollama",
        provider_type: "ollama",
        model: "nomic-embed-text",
        source: "embedding",
      },
    ],
  },
  "/api/v1/models/configuration": {
    path: "~/.local_openclaw/models.json",
    saved: false,
    api_keys_present: {},
  },
};

const VALID_TOKEN = "valid-token";

beforeEach(() => {
  window.localStorage.clear();
  useAuthStore.setState({ token: null, rejected: false });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const body = responses[url];
      const headers = (init?.headers ?? {}) as Record<string, string>;

      // Like the backend: everything but /health needs the token.
      if (
        url !== "/api/v1/health" &&
        headers.Authorization !== `Bearer ${VALID_TOKEN}`
      ) {
        return new Response(JSON.stringify({ detail: "Missing or wrong API token." }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (!body) {
        return new Response(JSON.stringify({ detail: "Not found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" },
        });
      }

      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  // The query cache is shared by every render; a result cached by one
  // test would otherwise answer the next test's requests.
  queryClient.clear();
  window.localStorage.clear();
  window.history.pushState(null, "", "/");
});

describe("App", () => {
  it("bootstraps the application shell", async () => {
    render(<App />);

    expect(
      screen.getByText("Repository Intelligence Platform"),
    ).toBeInTheDocument();

    // Signed out is not shown as the backend being down.
    await waitFor(() => {
      expect(
        screen.getByText("Backend connected · not signed in"),
      ).toBeInTheDocument();
    });
  });

  it("asks to sign in until it has a token, then shows the app", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Sign in to RIP" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("API token"), {
      target: { value: VALID_TOKEN },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    fireEvent.click(screen.getByRole("link", { name: "Settings" }));

    expect(
      await screen.findByRole("heading", { name: "Settings" }),
    ).toBeInTheDocument();
  });

  it("asks to sign in again when the backend rejects the saved token", async () => {
    useAuthStore.setState({ token: "old-token" });

    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "Settings" }));

    expect(
      await screen.findByText(/did not accept the saved token/),
    ).toBeInTheDocument();
  });

  it("stores the token from a sign-in link and removes it from the address bar", () => {
    window.history.pushState(null, "", "/editing?token=from-link");

    captureTokenFromUrl();

    expect(useAuthStore.getState().token).toBe("from-link");
    expect(window.location.pathname).toBe("/editing");
    expect(window.location.search).toBe("");
  });

  it("routes to workspace pages", async () => {
    useAuthStore.setState({ token: VALID_TOKEN });

    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "Settings" }));

    expect(
      await screen.findByRole("heading", { name: "Settings" }),
    ).toBeInTheDocument();
    // "qwen3.6" is both a picker option and a table cell; check the table.
    expect(await screen.findByRole("cell", { name: "qwen3.6" })).toBeInTheDocument();

    // The effective-model table resolves operations to models.
    expect(await screen.findByText("nomic-embed-text")).toBeInTheDocument();

    // The project page is labelled "Repository" in the sidebar.
    fireEvent.click(screen.getByRole("link", { name: "Repository" }));

    expect(
      await screen.findByRole("heading", { name: "Repository" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Project root directory")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Editing" }));

    expect(
      await screen.findByRole("heading", { name: "Editing" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No project open")).toBeInTheDocument();
  });
});
