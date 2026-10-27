/** Routes for guests only — logged-in users are sent to their dashboard. */
export const GUEST_ONLY_PATHS = [
  "/login",
  "/sign-in",
  "/register",
  "/forgot-password",
  "/reset-password",
] as const;

export function isGuestOnlyRoute(pathname: string): boolean {
  return (GUEST_ONLY_PATHS as readonly string[]).includes(pathname);
}
