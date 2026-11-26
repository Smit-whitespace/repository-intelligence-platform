import { Wifi, WifiOff } from "lucide-react";
import { useBackendHealth, useSystemStatus } from "@/lib/api/queries";
import { useAuthStore } from "@/stores/authStore";
import { useProjectStore } from "@/stores/projectStore";

export function StatusBar() {
  const signedIn = useAuthStore((state) => state.token !== null && !state.rejected);
  // /health needs no token, so "not signed in" is never shown as "backend down".
  const health = useBackendHealth();
  const { data } = useSystemStatus({ enabled: signedIn });
  const activeProject = useProjectStore((state) => state.activeProject);
  const connected = health.data?.status === "healthy";

  return (
    <footer className="flex items-center justify-between border-t border-[rgba(255,255,255,0.06)] bg-[#111827] px-4 text-xs text-[#7A8599]">
      <div className="flex items-center gap-2">
        {connected ? (
          <Wifi className="h-3.5 w-3.5 text-[#10B981]" aria-hidden="true" />
        ) : (
          <WifiOff className="h-3.5 w-3.5 text-[#EF4444]" aria-hidden="true" />
        )}
        <span>
          {health.isLoading
            ? "Checking backend"
            : connected
              ? signedIn
                ? "Backend connected"
                : "Backend connected · not signed in"
              : health.isError
                ? "Backend unavailable"
                : "Backend status unknown"}
        </span>
      </div>
      <span className="min-w-0 truncate">
        {activeProject ? `${activeProject.name} — ` : ""}
        {signedIn && data ? `${data.active_provider}: ${data.active_model}` : "No model"}
      </span>
    </footer>
  );
}
