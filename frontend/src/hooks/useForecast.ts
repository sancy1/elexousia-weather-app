/**
 * useForecast Hook
 * Custom hook for fetching weather forecast data
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/weather";
import type { ForecastResponse } from "@/lib/api-types";

export function useForecast(city: string, enabled: boolean = true, days: number = 7) {
  return useQuery({
    queryKey: ["weather", "forecast", city, days],
    queryFn: async () => {
      try {
        console.log(`Fetching forecast for city: ${city}, days: ${days}`);
        const data = await weatherApi.getForecast(city, days);
        console.log("Forecast data received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to fetch forecast for ${city}:`, error);
        throw error;
      }
    },
    enabled: enabled && !!city,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 1,
  });
}
