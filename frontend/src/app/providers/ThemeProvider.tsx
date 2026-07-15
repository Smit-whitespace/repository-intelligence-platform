import { useEffect } from "react";
import type { ReactNode } from "react";
import { useThemeStore } from "@/stores/themeStore";

type ThemeProviderProps = {
  children: ReactNode;
};

export function ThemeProvider({ children }: ThemeProviderProps) {
  const theme = useThemeStore((state) => state.theme);

  useEffect(() => {
    const root = document.documentElement;
    const systemDark =
      window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
    const shouldUseDark = theme === "dark" || (theme === "system" && systemDark);

    root.classList.toggle("dark", shouldUseDark);
  }, [theme]);

  return children;
}
