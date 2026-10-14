"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { getDashboardPath, normalizeRole } from "@/lib/roles";
import type { User } from "@/types";

function normalizeUser(raw: User): User {
  return { ...raw, role: normalizeRole(raw.role) };
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      authApi.me()
        .then(({ data }) => setUser(normalizeUser(data)))
        .catch(() => localStorage.clear())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login({ email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    queryClient.clear();
    const loggedIn = normalizeUser(data.user);
    setUser(loggedIn);
    return loggedIn;
  };

  const refreshUser = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const { data } = await authApi.me();
    setUser(normalizeUser(data));
  };

  const logout = () => {
    const refresh = localStorage.getItem("refresh_token");
    if (refresh) authApi.logout(refresh).catch(() => {});
    queryClient.clear();
    localStorage.clear();
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
