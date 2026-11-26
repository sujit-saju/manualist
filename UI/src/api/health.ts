import type { paths } from "./schema";

const livenessPath = "/api/v1/health/live" satisfies keyof paths;
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const healthQueryKeys = { live: ["health", "live"] } as const;

export async function getLiveness(): Promise<boolean> {
  const response = await fetch(new URL(livenessPath, apiBaseUrl));
  if (!response.ok) throw new Error("Liveness check failed");
  return true;
}
