"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/hooks/useAuth";
import { Navbar } from "@/components/layout/Navbar";
import { AuthRealtimeSync } from "@/components/layout/AuthRealtimeSync";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AuthRealtimeSync />
        <Navbar />
        <main className="min-h-[calc(100vh-3.5rem)]">{children}</main>
      </AuthProvider>
    </QueryClientProvider>
  );
}
