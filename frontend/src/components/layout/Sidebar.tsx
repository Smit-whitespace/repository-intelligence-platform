import {
  Bot,
  Code2,
  FolderGit2,
  Library,
  PanelLeftClose,
  PenTool,
  Search,
  Settings,
} from "lucide-react";
import { NavLink } from "react-router";
import { cn } from "@/lib/utils/cn";
import { useUiStore } from "@/stores/uiStore";

const navItems = [
  { to: "/projects", label: "Repository", icon: FolderGit2 },
  { to: "/chat", label: "Chat", icon: Bot },
  { to: "/repository", label: "Search", icon: Search },
  { to: "/editing", label: "Editing", icon: PenTool },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const collapsed = useUiStore((state) => state.sidebarCollapsed);

  if (collapsed) return null;

  return (
    <aside className="flex flex-col border-r border-[rgba(255,255,255,0.06)] bg-[#0A0F1E]">
      <div className="flex h-14 items-center gap-3 border-b border-[rgba(255,255,255,0.06)] px-4">
        <img
          src="/logo.png"
          alt="RIP"
          className="h-6 w-6 shrink-0"
        />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-[#F8FAFC]">RIP</p>
          <p className="truncate text-[11px] text-[#7A8599]">
            Repository Intelligence Platform
          </p>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 px-2 py-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "group relative flex h-9 items-center gap-3 rounded-[8px] px-3 text-sm transition-all duration-150",
                "text-[#7A8599] hover:bg-[rgba(255,255,255,0.04)] hover:text-[#F8FAFC]",
                isActive && "bg-[rgba(79,140,255,0.08)] text-[#F8FAFC]",
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1/2 h-4 w-[2.5px] -translate-y-1/2 rounded-r-full bg-gradient-to-b from-[#4F8CFF] to-[#8B5CF6]" />
                )}
                <item.icon
                  className={cn(
                    "h-[18px] w-[18px] shrink-0 transition-colors duration-150",
                    isActive ? "text-[#4F8CFF]" : "text-[#7A8599]",
                  )}
                  aria-hidden="true"
                />
                <span className="text-sm">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-[rgba(255,255,255,0.06)] p-3">
        <a
          href="https://github.com/Smit-whitespace/repository-intelligence-platform"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-[8px] px-3 py-2 text-xs text-[#7A8599] transition hover:bg-[rgba(255,255,255,0.04)] hover:text-[#F8FAFC]"
        >
          <Code2 className="h-3.5 w-3.5" />
          v0.1.0
        </a>
      </div>
    </aside>
  );
}
