/**
 * Authentication Helpers
 * Functions for managing authentication state and OAuth flows
 */

import { apiClient } from "./api-client";
import { env } from "./env";
import type { UserProfile, PreferencesUpdate } from "./api-types";

/**
 * Auth API endpoints
 */
export const authApi = {
  /**
   * Initiate Google OAuth login
   * Redirects to Google OAuth consent screen
   */
  loginWithGoogle: () => {
    window.location.href = `${env.API_BASE_URL}/api/auth/google`;
  },

  /**
   * Initiate GitHub OAuth login
   * Redirects to GitHub OAuth consent screen
   */
  loginWithGitHub: () => {
    window.location.href = `${env.API_BASE_URL}/api/auth/github`;
  },

  /**
   * Get current user profile
   * Requires valid session cookie
   */
  getCurrentUser: async (): Promise<UserProfile> => {
    return apiClient.get<UserProfile>("/api/auth/me");
  },

  /**
   * Update user preferences
   */
  updatePreferences: async (preferences: PreferencesUpdate): Promise<UserProfile> => {
    return apiClient.patch<UserProfile>("/api/auth/preferences", preferences);
  },

  /**
   * Logout user
   * Deletes session and clears cookie
   */
  logout: async (): Promise<{ success: boolean; message: string }> => {
    return apiClient.delete<{ success: boolean; message: string }>("/api/auth/logout");
  },

  /**
   * Get debug token (for development/testing)
   */
  getDebugToken: async (): Promise<{ session_token: string | null; user_id: number; email: string; note: string }> => {
    return apiClient.get<{ session_token: string | null; user_id: number; email: string; note: string }>("/api/auth/debug/token");
  },
};

/**
 * Check if user is authenticated
 * This is a client-side check - actual validation happens on the server
 */
export const isAuthenticated = (): boolean => {
  // We can't directly check HTTP-only cookies from JavaScript
  // This is a basic check - real validation should be done via API calls
  return document.cookie.includes("session_token");
};

/**
 * Get auth callback URL
 */
export const getAuthCallbackUrl = (provider: "google" | "github", success: boolean = true): string => {
  return `/auth/callback?provider=${provider}&success=${success}`;
};
