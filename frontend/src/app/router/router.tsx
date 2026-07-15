import { createBrowserRouter, Navigate } from "react-router";
import { AppShell } from "@/components/layout/AppShell";
import { ChatPage } from "@/features/chat/ChatPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { EditingPage } from "@/features/editing/EditingPage";
import { ProjectsPage } from "@/features/projects/ProjectsPage";
import { RepositoryPage } from "@/features/repository/RepositoryPage";
import { SettingsPage } from "@/features/settings/SettingsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "projects", element: <ProjectsPage /> },
      { path: "repository", element: <RepositoryPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "editing", element: <EditingPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);
