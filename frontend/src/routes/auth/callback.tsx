/**
 * OAuth Callback Route
 * Handles OAuth redirects from Google/GitHub
 */
import React from "react";
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/auth/callback")({
  // Define and validate the search parameters for type safety
  validateSearch: (search: Record<string, unknown>) => {
    return {
      success: search.success === "true" || search.success === true,
      error: search.error as string | undefined,
    };
  },
  component: AuthCallback,
});

function AuthCallback() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  
  // Get typed search parameters
  const { success, error } = useSearch({ from: "/auth/callback" });

  React.useEffect(() => {
    async function handleCallback() {
      if (success) {
        try {
          console.log("OAuth callback: Refreshing user session...");
          await refreshUser();
          
          // Small delay to allow AuthContext state to propagate
          await new Promise((resolve) => setTimeout(resolve, 500));
          
          console.log("OAuth callback: Success. Navigating to dashboard.");
          // SPA-friendly redirect
          navigate({ to: "/" });
        } catch (err) {
          console.error("OAuth callback error during refresh:", err);
          navigate({ to: "/", search: { auth: "error" } });
        }
      } else {
        // OAuth failed or was canceled
        console.warn("OAuth callback: Failed or error received:", error);
        navigate({ to: "/", search: { auth: "failed" } });
      }
    }

    handleCallback();
  }, [success, error, refreshUser, navigate]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground">
      <div className="relative flex flex-col items-center">
        {/* Glow effect background */}
        <div className="absolute -z-10 h-32 w-32 rounded-full bg-primary/20 blur-3xl animate-pulse" />
        
        <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary" />
        
        <h2 className="text-xl font-semibold tracking-tight">
          {success ? "Finalizing Login" : "Processing Authentication"}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {success 
            ? "Syncing your profile, please wait..." 
            : "Verifying credentials..."}
        </p>
      </div>
    </div>
  );
}