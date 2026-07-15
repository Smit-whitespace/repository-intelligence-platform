import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ProjectInfo } from "@/types/api";

type ProjectState = {
  activeProject: ProjectInfo | null;
  setActiveProject: (project: ProjectInfo) => void;
  clearActiveProject: () => void;
};

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      activeProject: null,
      setActiveProject: (project) =>
        set({
          activeProject: project,
        }),
      clearActiveProject: () =>
        set({
          activeProject: null,
        }),
    }),
    {
      name: "rip-active-project",
    },
  ),
);
