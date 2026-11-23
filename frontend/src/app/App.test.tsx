import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

beforeEach(() => {
  window.localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const body = responses[url];

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
  window.localStorage.clear();
  window.history.pushState(null, "", "/");
});

describe("App", () => {
  it("bootstraps the application shell", async () => {
    render(<App />);

    expect(
      screen.getByText("Repository Intelligence Platform"),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Backend connected")).toBeInTheDocument();
    });
  });

  it("routes to workspace pages", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("link", { name: "Settings" }));

    expect(
      await screen.findByRole("heading", { name: "Settings" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("qwen3.6")).toBeInTheDocument();

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
