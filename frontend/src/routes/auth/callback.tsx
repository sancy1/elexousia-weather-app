/**
 * OAuth Callback Route
 * Handles OAuth redirects from Google/GitHub
 */

import React from "react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { useAuth } from "@/contexts/AuthContext";

export const Route = createFileRoute("/auth/callback")({
  component: AuthCallback,
});

function AuthCallback() {
  const { refreshUser } = useAuth();
  const searchParams = new URLSearchParams(window.location.search);
  const success = searchParams.get("success") === "true";

  React.useEffect(() => {
    async function handleCallback() {
      if (success) {
        try {
          // Refresh user data to get the new session
          console.log("OAuth callback: Refreshing user...");
          await refreshUser();
          console.log("OAuth callback: User refreshed, redirecting...");
          // Small delay to ensure state update completes
          await new Promise(resolve => setTimeout(resolve, 500));
          // Redirect to home
          window.location.href = "/";
        } catch (error) {
          console.error("OAuth callback error:", error);
          window.location.href = "/?auth=error";
        }
      } else {
        // OAuth failed - redirect to home with error
        console.log("OAuth callback: Failed");
        window.location.href = "/?auth=failed";
      }
    }

    handleCallback();
  }, [success, refreshUser]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
        <p className="text-muted-foreground">
          {success ? "Completing authentication..." : "Authentication failed..."}
        </p>
      </div>
    </div>
  );
}
