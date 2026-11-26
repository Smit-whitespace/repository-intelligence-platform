import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * The API token (ADR-0020). The backend prints a sign-in link with
 * `?token=...` when it starts; opening it stores the token here, and
 * every API request sends it as `Authorization: Bearer <token>`.
 */
type AuthState = {
  token: string | null;
  /** Set when the backend refused the stored token (or there is none). */
  rejected: boolean;
  setToken: (token: string) => void;
  markRejected: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      rejected: false,
      setToken: (token) => set({ token: token.trim(), rejected: false }),
      markRejected: () => set({ rejected: true }),
    }),
    {
      name: "rip-api-token",
      partialize: (state) => ({ token: state.token }),
    },
  ),
);

/**
 * Store a token passed in the address bar, then remove it from the URL so
 * it is not left in history, bookmarks or screenshots.
 */
export function captureTokenFromUrl(location: Location = window.location) {
  const url = new URL(location.href);
  const token = url.searchParams.get("token");

  if (!token) {
    return;
  }

  useAuthStore.getState().setToken(token);
  url.searchParams.delete("token");
  window.history.replaceState(window.history.state, "", url.toString());
}

export function authorizationHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;

  return token ? { Authorization: `Bearer ${token}` } : {};
}
