import { describe, expect, it } from "vitest";
import { useProjectStore } from "./projectStore";

describe("projectStore", () => {
  it("stores and clears the active project", () => {
    useProjectStore.persist.clearStorage();
    useProjectStore.getState().clearActiveProject();

    useProjectStore.getState().setActiveProject({
      name: "example",
      root_directory: "A:/repo",
      storage_directory: "A:/repo/.local_openclaw",
      created_at: "2026-07-15T10:30:00Z",
    });

    expect(useProjectStore.getState().activeProject?.name).toBe("example");

    useProjectStore.getState().clearActiveProject();

    expect(useProjectStore.getState().activeProject).toBeNull();
  });
});
