"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getDashboardPath } from "@/lib/roles";
import { RoleBadge } from "@/components/account/RoleBadge";
import { Shield, LogOut, LayoutDashboard } from "lucide-react";
import { NotificationBell } from "@/components/layout/NotificationBell";
import { SIDEBAR_WIDTH } from "@/components/layout/PortalSidebar";

const PORTAL_PREFIXES = ["/dashboard", "/complaints", "/profile", "/notifications", "/officer", "/admin"];

import { isGuestOnlyRoute } from "@/lib/authRoutes";

function isPortalPage(pathname: string) {
  return PORTAL_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

function isAccountProfilePage(pathname: string) {
  return pathname === "/profile" || pathname.endsWith("/account");
}

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  if (isGuestOnlyRoute(pathname)) {
    return null;
  }

  const inPortal = user && isPortalPage(pathname);

  const logo = (
    <Link href={user ? getDashboardPath(user.role) : "/"} className="flex items-center gap-2.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
        <Shield className="h-4 w-4 text-white" />
      </div>
      <span className="font-semibold text-foreground">Civic Complaints</span>
    </Link>
  );

  const actions = user ? (
    <>
      {!inPortal && (
        <Link href={getDashboardPath(user.role)}>
          <Button variant="ghost" size="sm" className="hidden sm:inline-flex gap-1.5 text-primary hover:text-primary hover:bg-primary/10">
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Button>
        </Link>
      )}
      <NotificationBell />
      {inPortal && !isAccountProfilePage(pathname) && (
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-1.5">
          <span className="text-sm font-medium text-foreground max-w-[140px] truncate">{user.full_name}</span>
          <RoleBadge role={user.role} size="sm" />
        </div>
      )}
      {!inPortal && (
        <>
          <div className="hidden sm:flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1.5">
            <span className="text-sm font-medium text-foreground">{user.full_name}</span>
            <RoleBadge role={user.role} size="sm" />
          </div>
          <Button variant="outline" size="sm" onClick={logout} className="gap-1.5 border-primary/20 hover:bg-primary/5">
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </>
      )}
    </>
  ) : (
    <>
      <Link href="/login">
        <Button variant="ghost" size="sm" className="text-primary hover:bg-primary/10">
          Log in
        </Button>
      </Link>
      <Link href="/sign-in">
        <Button size="sm">Sign in</Button>
      </Link>
    </>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-white">
      {inPortal ? (
        <div className="mx-auto flex h-14 w-full max-w-7xl">
          <div className={cn("hidden md:flex shrink-0 items-center border-r border-border bg-white px-5", SIDEBAR_WIDTH)}>
            {logo}
          </div>
          <div className="flex flex-1 items-center justify-between gap-4 px-4 sm:px-6 bg-white">
            <div className="md:hidden">{logo}</div>
            <div className="hidden md:block" />
            <nav className="flex items-center gap-1.5 ml-auto">{actions}</nav>
          </div>
        </div>
      ) : (
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-4 sm:px-6">
          {logo}
          <nav className="flex items-center gap-1.5">{actions}</nav>
        </div>
      )}
    </header>
  );
}
