import { useQuery } from "@tanstack/react-query";

import { getLiveness, healthQueryKeys } from "../api/health";

const copy = {
  pending: "Checking the API…",
  success: "API reachable",
  error: "API unreachable",
} as const;

export function App() {
  const health = useQuery({
    queryKey: healthQueryKeys.live,
    queryFn: getLiveness,
    retry: false,
  });

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold text-slate-900">Manualist</h1>
      <p aria-live="polite" className="mt-4 text-slate-700">
        {copy[health.status]}
      </p>
    </main>
  );
}
