import { afterEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/stores/authStore";
import { bootstrap } from "./bootstrap";

afterEach(() => {
  vi.unstubAllGlobals();
  useAuthStore.setState({ token: null, rejected: false, linkError: null });
  window.history.pushState(null, "", "/");
});

describe("bootstrap", () => {
  it("renders only after the sign-in code has been exchanged", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ token: "from-code" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    window.history.pushState(null, "", "/?code=abc");

    const tokenAtRender: Array<string | null> = [];

    await bootstrap(() => tokenAtRender.push(useAuthStore.getState().token));

    // Graphify on #6: the app used to render first and send its first
    // requests without a token.
    expect(tokenAtRender).toEqual(["from-code"]);
  });

  it("still renders when the exchange fails, so the reason can be shown", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    window.history.pushState(null, "", "/?code=abc");

    const render = vi.fn();

    await bootstrap(render);

    expect(render).toHaveBeenCalledOnce();
    expect(useAuthStore.getState().linkError).toMatch(/Could not reach/);
  });

  it("renders straight away without a code", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const render = vi.fn();

    await bootstrap(render);

    expect(render).toHaveBeenCalledOnce();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
