import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { HeartPulse, ShieldCheck, ShieldAlert, Activity } from "lucide-react";

export const Route = createFileRoute("/health")({
  component: HealthComponent,
});

interface HealthData {
  status: string;
  backend?: any;
  error?: string;
  timestamp: string;
}

function HealthComponent() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      // Use VITE_API_URL if available, otherwise fallback to local
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      
      try {
        const response = await fetch(`${apiUrl}/api/health`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(`Backend responded with status: ${response.status}`);
        }

        const data = await response.json();
        setHealth({
          status: "healthy",
          backend: data,
          timestamp: new Date().toISOString(),
        });
      } catch (error) {
        setHealth({
          status: "unhealthy",
          error: error instanceof Error ? error.message : "Connection refused",
          timestamp: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-foreground">
      <div className="w-full max-w-2xl overflow-hidden rounded-3xl border border-border bg-card shadow-2xl">
        <div className="border-b border-border bg-muted/50 p-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2 text-primary">
              <HeartPulse className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">System Integrity</h1>
              <p className="text-sm text-muted-foreground">Real-time health status of EL-Exousia services</p>
            </div>
          </div>
        </div>

        <div className="p-8">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-10 space-y-4">
              <Activity className="h-10 w-10 animate-pulse text-primary" />
              <p className="text-sm font-medium animate-pulse">Probing backend services...</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between rounded-2xl border border-border p-4 bg-muted/30">
                <div className="flex items-center gap-3">
                  {health?.status === "healthy" ? (
                    <ShieldCheck className="h-8 w-8 text-green-500" />
                  ) : (
                    <ShieldAlert className="h-8 w-8 text-destructive" />
                  )}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Overall Status</p>
                    <p className={`text-lg font-bold ${health?.status === "healthy" ? "text-green-500" : "text-destructive"}`}>
                      {health?.status === "healthy" ? "OPERATIONAL" : "DEGRADED"}
                    </p>
                  </div>
                </div>
                <div className="text-right text-xs text-muted-foreground">
                  <p>Last Checked</p>
                  <p>{health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "N/A"}</p>
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Raw Diagnostic Data</p>
                <pre className="max-h-64 overflow-auto rounded-xl bg-black/90 p-4 font-mono text-[13px] text-green-400 scrollbar-thin">
                  {JSON.stringify(health, null, 2)}
                </pre>
              </div>

              <button
                onClick={() => window.location.reload()}
                className="w-full rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90 hover:shadow-lg"
              >
                Refresh Diagnostics
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}