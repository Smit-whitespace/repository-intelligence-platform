import { afterEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/stores/authStore";
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

  it("sends the API token and asks to sign in again when it is refused", async () => {
    useAuthStore.setState({ token: "secret", rejected: false });

    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ detail: "Missing or wrong API token." }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    vi.stubGlobal("fetch", fetchMock);

    await expect(request("/system/version")).rejects.toMatchObject({ status: 401 });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/system/version",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer secret" }),
      }),
    );
    expect(useAuthStore.getState().rejected).toBe(true);

    useAuthStore.setState({ token: null, rejected: false });
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
