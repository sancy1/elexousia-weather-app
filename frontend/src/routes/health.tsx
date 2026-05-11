import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/health")({
  loader: async () => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    
    try {
      const response = await fetch(`${apiUrl}/api/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Backend health check failed: ${response.status}`);
      }

      const data = await response.json();
      return {
        status: "healthy",
        backend: data,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        status: "unhealthy",
        error: error instanceof Error ? error.message : "Unknown error",
        timestamp: new Date().toISOString(),
      };
    }
  },
});
