import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./errors";
import { request } from "./httpClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("request", () => {
  it("returns parsed JSON from the configured API base", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ status: "healthy" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    vi.stubGlobal("fetch", fetchMock);

    await expect(request<{ status: string }>("/health")).resolves.toEqual({
      status: "healthy",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/health",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
  });

  it("translates backend errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: "Backend unavailable" }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(request("/health")).rejects.toBeInstanceOf(ApiError);
    await expect(request("/health")).rejects.toMatchObject({
      message: "Backend unavailable",
      status: 500,
    });
  });
});
