/**
 * useAutoDetect Hook
 * Custom hook for auto-detecting location and getting weather
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/weather";
import type { AutoWeatherResponse } from "@/lib/api-types";

export function useAutoDetect(enabled: boolean = true) {
  return useQuery({
    queryKey: ["weather", "auto"],
    queryFn: async () => {
      try {
        console.log("Auto-detecting location...");
        const data = await weatherApi.autoDetect();
        console.log("Auto-detect success:", data);
        return data;
      } catch (error) {
        console.error("Auto-detect failed:", error);
        throw error;
      }
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 0, // Don't retry auto-detect (will fail on localhost)
  });
}
