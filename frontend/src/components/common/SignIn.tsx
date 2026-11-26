import { KeyRound } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { queryClient } from "@/lib/api/queryClient";
import { useAuthStore } from "@/stores/authStore";

/** Shown until the app has an API token the backend accepts (ADR-0020). */
export function SignIn() {
  // Only a token that was sent can have been rejected.
  const rejected = useAuthStore((state) => state.rejected && state.token !== null);
  const linkError = useAuthStore((state) => state.linkError);
  const setToken = useAuthStore((state) => state.setToken);
  const [value, setValue] = useState("");

  return (
    <section className="animate-fade-in mx-auto max-w-xl rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-6">
      <div className="flex items-center gap-2">
        <KeyRound className="h-4 w-4 text-[#4F8CFF]" aria-hidden="true" />
        <h1 className="text-base font-semibold text-[#F8FAFC]">Sign in to RIP</h1>
      </div>
      <p className="mt-3 text-sm text-[#AAB4C5]">
        {rejected
          ? "The backend did not accept the saved token. It may have been replaced."
          : "The RIP backend only answers this app once it has your API token."}
      </p>
      {linkError ? (
        <p role="alert" className="mt-3 text-sm text-[#FBBF24]">
          {linkError}
        </p>
      ) : null}
      <p className="mt-3 text-sm text-[#AAB4C5]">
        Open the sign-in link the backend printed when it started (the{" "}
        <code className="break-anywhere font-mono text-xs text-[#22D3EE]">
          open_this_link
        </code>{" "}
        line; it works once, for ten minutes), or paste the token from{" "}
        <code className="break-anywhere font-mono text-xs text-[#22D3EE]">
          ~/.local_openclaw/api.token
        </code>
        .
      </p>
      <form
        className="mt-4 flex flex-col gap-3 md:flex-row"
        onSubmit={(event) => {
          event.preventDefault();

          if (!value.trim()) {
            return;
          }

          setToken(value);
          setValue("");
          void queryClient.invalidateQueries();
        }}
      >
        <label htmlFor="apiToken" className="sr-only">
          API token
        </label>
        <input
          id="apiToken"
          type="password"
          autoComplete="off"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Paste the API token"
          className="h-10 min-w-0 flex-1 rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.1)] bg-[#0A0F1E] px-3 text-sm text-[#F8FAFC] placeholder-[#7A8599] outline-none transition focus:border-[#4F8CFF]/50"
        />
        <Button type="submit" disabled={!value.trim()}>
          Sign in
        </Button>
      </form>
    </section>
  );
}
