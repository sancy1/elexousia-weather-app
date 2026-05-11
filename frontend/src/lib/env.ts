/**
 * Environment configuration
 * Centralized environment variable access with type safety
 */

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value || defaultValue || "";
};

export const env = {
  // API Configuration
  API_BASE_URL: getEnvVar("VITE_API_BASE_URL", "http://localhost:8000"),
  
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
