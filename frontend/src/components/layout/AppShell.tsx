import { Outlet } from "react-router";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { StatusBar } from "./StatusBar";

export function AppShell() {
  return (
    <div className="grid min-h-screen grid-cols-[240px_1fr] bg-background text-foreground">
      <Sidebar />
      <div className="grid min-h-screen grid-rows-[56px_1fr_36px]">
        <Header />
        <main className="overflow-auto p-6">
          <Outlet />
        </main>
        <StatusBar />
      </div>
    </div>
  );
}
