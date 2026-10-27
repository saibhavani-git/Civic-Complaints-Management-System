"use client";

import Image from "next/image";
import { Shield } from "lucide-react";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  /** Show civic complaint hero on the left panel (login). */
  showComplaintHero?: boolean;
}

export function AuthLayout({ title, subtitle, children, showComplaintHero }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen">
      <div className="relative hidden lg:flex lg:w-1/2 flex-col justify-between overflow-hidden bg-primary p-12 text-white">
        {showComplaintHero && (
          <>
            <Image
              src="/images/login-complaint-hero.svg"
              alt=""
              fill
              priority
              className="object-cover object-center opacity-40"
              aria-hidden
            />
            <div className="absolute inset-0 bg-gradient-to-t from-primary via-primary/80 to-primary/60" aria-hidden />
          </>
        )}
        <div className="relative z-10" aria-hidden={showComplaintHero ? true : undefined}>
          {!showComplaintHero ? <div className="h-9" /> : null}
        </div>
        <div className="relative z-10">
          <h2 className="text-3xl font-semibold leading-tight">
            Report issues.<br />Track resolution.<br />Build better cities.
          </h2>
          <p className="mt-4 text-blue-100 max-w-md">
            AI-powered grievance management for faster, transparent civic issue resolution.
          </p>
        </div>
        <p className="relative z-10 text-sm text-blue-200">Government of India — Smart Governance Initiative</p>
      </div>

      <div className="flex flex-1 items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold">Civic Complaints</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
