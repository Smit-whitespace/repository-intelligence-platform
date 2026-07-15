import { PanelLeft, SunMoon } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useThemeStore, type ThemeMode } from "@/stores/themeStore";
import { useUiStore } from "@/stores/uiStore";

const themeOptions: ThemeMode[] = ["light", "dark", "system"];

export function Header() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <header className="flex items-center justify-between border-b border-border bg-background px-4">
      <div className="flex items-center gap-3">
        <Button
          aria-label="Toggle sidebar"
          className="h-8 w-8 bg-muted p-0 text-foreground"
          onClick={toggleSidebar}
        >
          <PanelLeft className="h-4 w-4" aria-hidden="true" />
        </Button>
        <h1 className="text-sm font-semibold">
          Repository Intelligence Platform (RIP)
        </h1>
      </div>
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <SunMoon className="h-4 w-4" aria-hidden="true" />
        <select
          value={theme}
          onChange={(event) => setTheme(event.target.value as ThemeMode)}
          className="h-8 rounded-md border border-border bg-background px-2 text-foreground"
        >
          {themeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </header>
  );
}
