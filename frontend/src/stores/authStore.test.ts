import { afterEach, describe, expect, it, vi } from "vitest";
import {
  SIGN_IN_TIMEOUT_MS,
  resetPendingSignInForTests,
  retrySignIn,
  signInFromUrl,
  useAuthStore,
} from "./authStore";

type Body = { code: string; verifier: string };

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function bodyOf(call: unknown[]): Body {
  return JSON.parse(String((call[1] as RequestInit).body)) as Body;
}

/** A backend that accepts a request but never answers (until aborted). */
function hangUntilAborted(_input: RequestInfo | URL, init?: RequestInit) {
  return new Promise<Response>((_resolve, reject) => {
    init?.signal?.addEventListener("abort", () =>
      reject(new DOMException("Aborted", "AbortError")),
    );
  });
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  resetPendingSignInForTests();
  useAuthStore.setState({ token: null, rejected: false, linkError: null, canRetry: false });
  window.sessionStorage.clear();
  window.history.pushState(null, "", "/");
});

describe("sign-in retry", () => {
  it("retries a timed-out sign-in with the same code and verifier", async () => {
    // Graphify on #7: the backend may have used the code when the app's
    // request timed out, so the token was lost and the link was spent.
    vi.useFakeTimers();

    const fetchMock = vi
      .fn()
      .mockImplementationOnce(hangUntilAborted)
      .mockResolvedValueOnce(json(200, { token: "the-token" }));

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState(null, "", "/?code=printed-code");

    const first = signInFromUrl();
    await vi.advanceTimersByTimeAsync(SIGN_IN_TIMEOUT_MS + 1);
    await first;

    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().canRetry).toBe(true);
    expect(window.location.search).toBe("");

    await retrySignIn();

    const [attempt, retry] = fetchMock.mock.calls.map(bodyOf);

    expect(retry).toEqual(attempt);
    expect(attempt.code).toBe("printed-code");
    expect(attempt.verifier.length).toBeGreaterThanOrEqual(16);
    expect(useAuthStore.getState().token).toBe("the-token");
    expect(useAuthStore.getState().canRetry).toBe(false);
    expect(window.sessionStorage.length).toBe(0);
  });

  it("retries a pending sign-in after a reload", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(json(200, { token: "the-token" }));

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState(null, "", "/?code=printed-code");

    await signInFromUrl();

    // The reload: no code in the URL any more.
    await signInFromUrl();

    const [attempt, retry] = fetchMock.mock.calls.map(bodyOf);

    expect(retry).toEqual(attempt);
    expect(useAuthStore.getState().token).toBe("the-token");
  });

  it("does not offer a retry when the code was refused", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(json(401, { detail: "already used" })),
    );
    window.history.pushState(null, "", "/?code=printed-code");

    await signInFromUrl();

    expect(useAuthStore.getState().canRetry).toBe(false);
    expect(window.sessionStorage.length).toBe(0);
  });

  it("signs in and can retry even when session storage is blocked", async () => {
    // Graphify on #8: with storage blocked the pending sign-in was never
    // saved, so the link silently did nothing.
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("Blocked", "SecurityError");
    });

    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(json(200, { token: "the-token" }));

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState(null, "", "/?code=printed-code");

    await signInFromUrl();

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(useAuthStore.getState().canRetry).toBe(true);

    await retrySignIn();

    const [attempt, retry] = fetchMock.mock.calls.map(bodyOf);

    expect(attempt.code).toBe("printed-code");
    expect(retry).toEqual(attempt);
    expect(useAuthStore.getState().token).toBe("the-token");
  });

  it("uses a new link, not an older pending one", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(json(200, { token: "the-token" }));

    vi.stubGlobal("fetch", fetchMock);

    window.history.pushState(null, "", "/?code=old-code");
    await signInFromUrl();

    window.history.pushState(null, "", "/?code=new-code");
    await signInFromUrl();

    expect(bodyOf(fetchMock.mock.calls[1]).code).toBe("new-code");
  });

  it("makes a new verifier for every link", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(401, { detail: "expired" }));

    vi.stubGlobal("fetch", fetchMock);

    window.history.pushState(null, "", "/?code=first");
    await signInFromUrl();
    window.history.pushState(null, "", "/?code=second");
    await signInFromUrl();

    const [first, second] = fetchMock.mock.calls.map(bodyOf);

    expect(first.verifier).not.toBe(second.verifier);
  });
});
