/**
 * useWeather Hook
 * Custom hook for fetching current weather data
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/weather";
import type { CurrentWeatherResponse } from "@/lib/api-types";

export function useWeather(city: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["weather", "current", city],
    queryFn: async () => {
      try {
        console.log(`Fetching weather for city: ${city}`);
        const data = await weatherApi.getCurrentWeather(city);
        console.log("Weather data received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to fetch weather for ${city}:`, error);
        throw error;
      }
    },
    enabled: enabled && !!city,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
}
