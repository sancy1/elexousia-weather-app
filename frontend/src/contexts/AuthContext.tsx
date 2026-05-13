/**
 * Authentication Context
 * Provides user authentication state and methods throughout the app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { authApi } from "@/lib/auth";
import type { UserProfile } from "@/lib/api-types";

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  loginWithGoogle: () => void;
  loginWithGitHub: () => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch current user on mount
   */
  useEffect(() => {
    refreshUser();
  }, []);

  /**
   * Refresh user data from API
   */
  const refreshUser = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching current user...");
      const userData = await authApi.getCurrentUser();
      console.log("User data received:", userData);
      setUser(userData);
    } catch (err) {
      // User might not be authenticated, which is okay
      console.error("Failed to fetch user:", err);
      setUser(null);
      setError(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Login with Google
   */
  const loginWithGoogle = () => {
    authApi.loginWithGoogle();
  };

  /**
   * Login with GitHub
   */
  const loginWithGitHub = () => {
    authApi.loginWithGitHub();
  };

  /**
   * Logout user
   */
  const logout = async () => {
    try {
      await authApi.logout();
      setUser(null);
      window.location.href = "/";
    } catch (error) {
      console.error("Logout failed:", error);
      setError("Failed to logout");
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    loginWithGoogle,
    loginWithGitHub,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to use auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
