import { Wifi, WifiOff } from "lucide-react";
import { useSystemStatus } from "@/lib/api/queries";
import { useProjectStore } from "@/stores/projectStore";

export function StatusBar() {
  const { data, isError, isLoading } = useSystemStatus();
  const activeProject = useProjectStore((state) => state.activeProject);
  const connected = data?.backend_health === "healthy";

  return (
    <footer className="flex items-center justify-between border-t border-[rgba(255,255,255,0.06)] bg-[#111827] px-4 text-xs text-[#7A8599]">
      <div className="flex items-center gap-2">
        {connected ? (
          <Wifi className="h-3.5 w-3.5 text-[#10B981]" aria-hidden="true" />
        ) : (
          <WifiOff className="h-3.5 w-3.5 text-[#EF4444]" aria-hidden="true" />
        )}
        <span>
          {isLoading
            ? "Checking backend"
            : connected
              ? "Backend connected"
              : isError
                ? "Backend unavailable"
                : "Backend status unknown"}
        </span>
      </div>
      <span className="min-w-0 truncate">
        {activeProject ? `${activeProject.name} — ` : ""}
        {data ? `${data.active_provider}: ${data.active_model}` : "No model"}
      </span>
    </footer>
  );
}
