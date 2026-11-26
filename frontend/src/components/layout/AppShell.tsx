import { Outlet } from "react-router";
import { SignIn } from "@/components/common/SignIn";
import { useAuthStore } from "@/stores/authStore";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { StatusBar } from "./StatusBar";

export function AppShell() {
  const signedIn = useAuthStore((state) => state.token !== null && !state.rejected);

  return (
    <div className="grid min-h-screen grid-cols-[240px_minmax(0,1fr)] bg-[#0A0F1E] text-[#F8FAFC]">
      <Sidebar />
      <div className="grid min-h-screen grid-rows-[56px_1fr_36px]">
        <Header />
        <main className="overflow-auto p-8">{signedIn ? <Outlet /> : <SignIn />}</main>
        <StatusBar />
      </div>
    </div>
  );
}
