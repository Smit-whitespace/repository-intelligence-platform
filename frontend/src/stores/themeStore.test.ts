import { describe, expect, it } from "vitest";
import { useThemeStore } from "./themeStore";

describe("themeStore", () => {
  it("initializes with system theme and updates theme", () => {
    useThemeStore.persist.clearStorage();
    useThemeStore.setState({ theme: "system" });

    expect(useThemeStore.getState().theme).toBe("system");

    useThemeStore.getState().setTheme("dark");

    expect(useThemeStore.getState().theme).toBe("dark");
  });
});
