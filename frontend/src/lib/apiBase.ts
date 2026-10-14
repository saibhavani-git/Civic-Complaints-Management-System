/** Backend origin (no /api/v1 suffix). Matches frontend/.env.local NEXT_PUBLIC_API_URL. */
export function getApiOrigin(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1";
  return raw.replace(/\/api\/v1\/?$/, "");
}

export function apiUnreachableMessage(): string {
  return `Cannot reach the API at ${getApiOrigin()}. Start the backend from backend\\venv (port 8002 or start-api.ps1), then restart \`npm run dev\`.`;
}
