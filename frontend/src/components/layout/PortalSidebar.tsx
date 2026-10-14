"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LogOut } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { User } from "@/types";
import { RoleBadge } from "@/components/account/RoleBadge";
import { normalizeRole } from "@/lib/roles";
import { fieldAreaTextClassName, officerServiceAreaLabel, userDepartmentLabel } from "@/lib/staffDisplay";

export const SIDEBAR_WIDTH = "w-64";

export interface NavLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

interface PortalSidebarProps {
  title: string;
  links: NavLink[];
  user: User;
  onLogout: () => void;
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function PortalSidebar({ title, links, user, onLogout }: PortalSidebarProps) {
  const pathname = usePathname();
  const initials = getInitials(user.full_name);
  const deptLabel = userDepartmentLabel(user);
  const fieldArea = officerServiceAreaLabel(user);
  const showStaffMeta = normalizeRole(user.role) === "officer" || normalizeRole(user.role) === "dept_admin";

  return (
    <>
      <aside
        className={cn(
          "hidden md:flex shrink-0 flex-col border-r border-border bg-white",
          SIDEBAR_WIDTH,
          "sticky top-14 h-[calc(100vh-3.5rem)]"
        )}
      >
        <div className="sidebar-header p-5">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-white/80">
            {title}
          </p>
          <div className="mt-4 flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold text-primary">
              {initials}
            </div>
            <div className="min-w-0 space-y-1">
              <p className="truncate text-sm font-semibold text-white">{user.full_name}</p>
              <RoleBadge role={user.role} size="sm" className="!ring-white/30" />
              {showStaffMeta && deptLabel && (
                <p className="truncate text-[11px] text-white/85 leading-tight">{deptLabel}</p>
              )}
              {fieldArea && (
                <p className={cn("text-[10px] text-white/75", fieldAreaTextClassName)}>
                  <span className="font-medium text-white/85">Field area: </span>
                  {fieldArea}
                </p>
              )}
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1 bg-[hsl(214,100%,98%)]">
          {links.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all",
                  active
                    ? "nav-active"
                    : "text-muted-foreground hover:bg-white hover:text-primary"
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", active ? "text-primary" : "")} />
                <span className="truncate">{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border bg-white p-3">
          <button
            onClick={onLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-red-50 hover:text-red-600"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            Sign out
          </button>
        </div>
      </aside>

      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t border-border bg-white flex safe-area-pb">
        {links.slice(0, 4).map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex-1 flex flex-col items-center justify-center gap-0.5 py-2.5 text-[10px] transition-colors",
                active ? "text-primary font-semibold bg-primary/5" : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

interface PortalFrameProps {
  sidebar: React.ReactNode;
  children: React.ReactNode;
}

export function PortalFrame({ sidebar, children }: PortalFrameProps) {
  return (
    <div className="mx-auto flex w-full max-w-7xl min-h-[calc(100vh-3.5rem)] theme-surface">
      {sidebar}
      <main className="flex-1 min-w-0 px-4 sm:px-6 py-6 pb-24 md:pb-6 overflow-auto">
        {children}
      </main>
    </div>
  );
}
