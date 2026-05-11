/**
 * useHourlyForecast Hook
 * Custom hook for fetching hourly forecast data
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/weather";
import type { HourlyForecastResponse } from "@/lib/api-types";

export function useHourlyForecast(city: string, date: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["weather", "hourly", city, date],
    queryFn: async () => {
      try {
        console.log(`Fetching hourly forecast for city: ${city}, date: ${date}`);
        const data = await weatherApi.getHourlyForecast(city, date);
        console.log("Hourly forecast received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to fetch hourly forecast for ${city}:`, error);
        // Return empty data on error to prevent UI from breaking
        return {
          city: city,
          date: date,
          hourly: []
        } as HourlyForecastResponse;
      }
    },
    enabled: enabled && !!city && !!date,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 0, // Don't retry hourly forecast
  });
}
