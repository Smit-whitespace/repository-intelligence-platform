import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./endpoints";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api endpoints", () => {
  it("opens projects and fetches repository indexes through the API client", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url === "/api/v1/projects/open") {
        return new Response(
          JSON.stringify({
            project: "example",
            root_directory: "A:/repo",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }

      return new Response(
        JSON.stringify({
          summary: {
            files: 1,
            directories: 0,
            total_size_bytes: 12,
          },
          entries: [],
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });

    vi.stubGlobal("fetch", fetchMock);

    await api.openProject({
      root_directory: "A:/repo",
    });
    await api.repositoryIndex("A:/repo");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/projects/open",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          root_directory: "A:/repo",
        }),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/repository/index?root_directory=A%3A%2Frepo",
      expect.any(Object),
    );
  });

  it("updates the active model through the settings endpoint", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          active_provider: "ollama",
          active_model: "qwen3.6",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    vi.stubGlobal("fetch", fetchMock);

    await api.updateActiveModel({
      model: "qwen3.6",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/settings/model",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({
          model: "qwen3.6",
        }),
      }),
    );
  });
});
