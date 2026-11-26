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
      setToken: (token) => set({ token: token.trim(), rejected: false, linkError: null }),
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

/**
 * Sign in from a link's single-use code. The code is removed from the
 * address bar first, so it is never left in history or bookmarks even if
 * the exchange fails.
 */
export async function signInFromUrl(location: Location = window.location) {
  const url = new URL(location.href);
  const code = url.searchParams.get("code");

  if (!code) {
    return;
  }

  url.searchParams.delete("code");
  window.history.replaceState(window.history.state, "", url.toString());

  const { setToken, setLinkError } = useAuthStore.getState();

  // The app waits for this before its first render, so a backend that
  // accepts the request but never answers must not leave the page blank.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), SIGN_IN_TIMEOUT_MS);

  try {
    const response = await fetch(`${config.apiBaseUrl}/auth/sign-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
      signal: controller.signal,
    });

    const payload = (await response.json().catch(() => ({}))) as {
      token?: unknown;
      detail?: unknown;
    };

    if (response.ok && typeof payload.token === "string") {
      setToken(payload.token);
      return;
    }

    setLinkError(
      typeof payload.detail === "string"
        ? payload.detail
        : `Sign-in failed with status ${response.status}.`,
    );
  } catch {
    setLinkError(
      controller.signal.aborted
        ? "The RIP backend did not answer the sign-in request in time. Check that it is running, then open the link again or paste the token."
        : "Could not reach the RIP backend to sign in. Is it running?",
    );
  } finally {
    clearTimeout(timer);
  }
}

export function authorizationHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;

  return token ? { Authorization: `Bearer ${token}` } : {};
}
