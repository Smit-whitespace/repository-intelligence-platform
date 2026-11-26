import { create } from "zustand";
import { persist } from "zustand/middleware";
import { config } from "@/lib/config/env";

/**
 * The API token (ADR-0020). The backend prints a sign-in link with a
 * single-use `?code=...` when it starts; the app exchanges the code for
 * the token once, stores it here, and sends it on every API request as
 * `Authorization: Bearer <token>`.
 */
type AuthState = {
  token: string | null;
  /** Set when the backend refused the stored token (or there is none). */
  rejected: boolean;
  /** Why the last sign-in link did not work, to show on the sign-in screen. */
  linkError: string | null;
  /** The last sign-in failed in a way a retry of the same link can fix. */
  canRetry: boolean;
  setToken: (token: string) => void;
  markRejected: () => void;
  setLinkError: (message: string | null) => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      rejected: false,
      linkError: null,
      canRetry: false,
      setToken: (token) =>
        set({ token: token.trim(), rejected: false, linkError: null, canRetry: false }),
      markRejected: () => set({ rejected: true }),
      setLinkError: (message) => set({ linkError: message }),
    }),
    {
      name: "rip-api-token",
      partialize: (state) => ({ token: state.token }),
    },
  ),
);

/** How long to wait for the sign-in exchange before showing the app anyway. */
export const SIGN_IN_TIMEOUT_MS = 10_000;

const PENDING_KEY = "rip-pending-sign-in";

/** A sign-in that has not succeeded yet: the link's code and our verifier. */
type PendingSignIn = { code: string; verifier: string };

/**
 * Kept in this tab's session storage until sign-in succeeds, so a request
 * that timed out (possibly after the backend used the code) can be retried
 * with the same verifier, which the backend accepts again. It never goes
 * in the URL, and it is dropped when the tab closes.
 */
function readPending(): PendingSignIn | null {
  try {
    const value = JSON.parse(window.sessionStorage.getItem(PENDING_KEY) ?? "null") as unknown;

    if (
      value &&
      typeof value === "object" &&
      typeof (value as PendingSignIn).code === "string" &&
      typeof (value as PendingSignIn).verifier === "string"
    ) {
      return value as PendingSignIn;
    }
  } catch {
    // Unreadable storage: treat as no pending sign-in.
  }

  return null;
}

function writePending(pending: PendingSignIn) {
  try {
    window.sessionStorage.setItem(PENDING_KEY, JSON.stringify(pending));
  } catch {
    // Without storage a retry is impossible, but signing in still works.
  }
}

function clearPending() {
  try {
    window.sessionStorage.removeItem(PENDING_KEY);
  } catch {
    // Nothing to clear.
  }
}

function newVerifier(): string {
  const bytes = window.crypto.getRandomValues(new Uint8Array(24));

  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

/**
 * Sign in from a link's single-use code. The code is removed from the
 * address bar first, so it is never left in history or bookmarks. Without
 * a code in the URL, a sign-in left pending by a timeout (for example
 * before a reload) is retried.
 */
export async function signInFromUrl(location: Location = window.location) {
  const url = new URL(location.href);
  const code = url.searchParams.get("code");

  if (code) {
    url.searchParams.delete("code");
    window.history.replaceState(window.history.state, "", url.toString());
    writePending({ code, verifier: newVerifier() });
  }

  await exchangePending();
}

/** Retry a sign-in that timed out or could not reach the backend. */
export async function retrySignIn() {
  await exchangePending();
}

async function exchangePending() {
  const pending = readPending();

  if (!pending) {
    return;
  }

  const { setToken, setLinkError } = useAuthStore.getState();

  // The app waits for this before its first render, so a backend that
  // accepts the request but never answers must not leave the page blank.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), SIGN_IN_TIMEOUT_MS);

  try {
    const response = await fetch(`${config.apiBaseUrl}/auth/sign-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pending),
      signal: controller.signal,
    });

    const payload = (await response.json().catch(() => ({}))) as {
      token?: unknown;
      detail?: unknown;
    };

    if (response.ok && typeof payload.token === "string") {
      clearPending();
      setToken(payload.token);
      return;
    }

    // A server error may be passing; anything else (used by another app,
    // expired, malformed) will not change on retry.
    const retryable = response.status >= 500;

    if (!retryable) {
      clearPending();
    }

    useAuthStore.setState({ canRetry: retryable });
    setLinkError(
      typeof payload.detail === "string"
        ? payload.detail
        : `Sign-in failed with status ${response.status}.`,
    );
  } catch {
    // The backend may have used the code and its answer got lost; the
    // pending code and verifier let a retry collect the token.
    useAuthStore.setState({ canRetry: true });
    setLinkError(
      controller.signal.aborted
        ? "The RIP backend did not answer the sign-in request in time. Check that it is running, then try again."
        : "Could not reach the RIP backend to sign in. Start it, then try again.",
    );
  } finally {
    clearTimeout(timer);
  }
}

export function authorizationHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;

  return token ? { Authorization: `Bearer ${token}` } : {};
}
