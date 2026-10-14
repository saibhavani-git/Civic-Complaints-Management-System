import axios from "axios";

/** User-facing message when GET /complaints fails (often backend 500). */
export function complaintsLoadErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (error.response?.status === 401) return "Session expired — log in again.";
    if (error.response?.status === 500) {
      return "The API crashed loading complaints — stop old servers and run backend\\start-api.ps1 (use venv on port 8000).";
    }
    if (error.response?.status) return `Could not load complaints (HTTP ${error.response.status}).`;
    if (error.code === "ERR_NETWORK") {
      return "Cannot reach the API — start the backend (backend\\start-api.ps1) and check NEXT_PUBLIC_API_URL in frontend/.env.local.";
    }
  }
  return "Could not load complaints. Start the backend and refresh.";
}
