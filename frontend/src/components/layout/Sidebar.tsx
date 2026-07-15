import {
  Bot,
  FolderOpen,
  GitBranch,
  Home,
  PenTool,
  Settings,
} from "lucide-react";
import { NavLink } from "react-router";
import { cn } from "@/lib/utils/cn";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: Home },
  { to: "/projects", label: "Projects", icon: FolderOpen },
  { to: "/repository", label: "Repository", icon: GitBranch },
  { to: "/chat", label: "Chat", icon: Bot },
  { to: "/editing", label: "Editing", icon: PenTool },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="border-r border-border bg-surface">
      <div className="flex h-14 items-center border-b border-border px-4">
        <div>
          <p className="text-sm font-semibold">RIP</p>
          <p className="text-xs text-muted-foreground">
            Repository Intelligence Platform
          </p>
        </div>
      </div>
      <nav className="space-y-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex h-9 items-center gap-2 rounded-md px-3 text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground",
                isActive && "bg-muted font-medium text-foreground",
              )
            }
          >
            <item.icon className="h-4 w-4" aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
