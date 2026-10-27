import { RedirectAuthenticatedToDashboard } from "@/components/auth/RedirectAuthenticatedToDashboard";

export default function AuthGroupLayout({ children }: { children: React.ReactNode }) {
  return <RedirectAuthenticatedToDashboard>{children}</RedirectAuthenticatedToDashboard>;
}
