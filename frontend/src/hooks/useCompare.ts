/**
 * useCompare Hook
 * Custom hook for comparing weather between two cities
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/weather";
import type { CompareWeatherResponse } from "@/lib/api-types";

export function useCompare(city1: string, city2: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["weather", "compare", city1, city2],
    queryFn: async () => {
      try {
        console.log(`Comparing cities: ${city1} vs ${city2}`);
        const data = await weatherApi.compareCities(city1, city2);
        console.log("Compare data received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to compare cities ${city1} and ${city2}:`, error);
        throw error;
      }
    },
    enabled: enabled && !!city1 && !!city2,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
}
