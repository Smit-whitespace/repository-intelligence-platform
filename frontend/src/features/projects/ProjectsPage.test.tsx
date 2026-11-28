import { act, fireEvent, render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { queryClient } from "@/lib/api/queryClient";
import { useProjectStore } from "@/stores/projectStore";
import { ProjectsPage } from "./ProjectsPage";

const project = {
  name: "repo",
  root_directory: "A:/repo",
  storage_directory: "A:/repo/.rip",
};

vi.mock("@/lib/api/endpoints", () => ({
  api: {
    openProject: vi.fn(async () => ({ root_directory: "A:/repo" })),
    projectInfo: vi.fn(async () => project),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), info: vi.fn() },
}));

beforeEach(() => {
  useProjectStore.setState({ activeProject: null } as never);
});

describe("ProjectsPage", () => {
  it("refreshes the index state after opening a project", async () => {
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectsPage />
      </QueryClientProvider>,
    );

    const input = screen.getByLabelText("Project root directory");

    await act(async () => {
      fireEvent.change(input, { target: { value: "A:/repo" } });
      fireEvent.submit(input.closest("form")!);
    });

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["workspace", "index-status", "A:/repo"],
    });
  });
});
