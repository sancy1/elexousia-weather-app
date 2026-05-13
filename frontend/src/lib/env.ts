/**
 * Environment configuration
 * Centralized environment variable access with type safety
 */

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key];
  // Return value or defaultValue, never throw to allow build to proceed
  return value !== undefined ? value : (defaultValue || "");
};

export const env = {
  // API Configuration
  // Local dev defaults to the API on localhost; production build falls back to Render.
  API_BASE_URL:
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL ||
    (import.meta.env.DEV
      ? "http://localhost:8000"
      : "https://elexousia-weather-app-backend.onrender.com"),

  // OAuth Configuration
  GOOGLE_OAUTH_ENABLED: getEnvVar("VITE_GOOGLE_OAUTH_ENABLED", "true") === "true",
  GITHUB_OAUTH_ENABLED: getEnvVar("VITE_GITHUB_OAUTH_ENABLED", "true") === "true",

  // Feature Flags
  ENABLE_IDE_MODE: getEnvVar("VITE_ENABLE_IDE_MODE", "false") === "true",
  ENABLE_AGENT_MODE: getEnvVar("VITE_ENABLE_AGENT_MODE", "false") === "true",

  // Environment
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
} as const;

export type Env = typeof env;
