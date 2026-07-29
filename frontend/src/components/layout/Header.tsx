import { PanelLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useUiStore } from "@/stores/uiStore";

export function Header() {
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <header className="flex h-14 items-center justify-between border-b border-[rgba(255,255,255,0.06)] bg-[#0A0F1E] px-6">
      <Button
        variant="ghost"
        aria-label="Toggle sidebar"
        className="h-8 w-8 p-0"
        onClick={toggleSidebar}
      >
        <PanelLeft className="h-4 w-4" />
      </Button>
      <div className="flex items-center gap-2 text-xs text-[#7A8599]">
        <span className="flex h-2 w-2 rounded-full bg-[#10B981]" />
        Online
      </div>
    </header>
  );
}
