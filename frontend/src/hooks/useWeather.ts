/**
 * useWeather Hook
 * Custom hook for fetching current weather data
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi, type Coords } from "@/lib/weather";
import type { CurrentWeatherResponse } from "@/lib/api-types";

export function useWeather(city: string, enabled: boolean = true, coords?: Coords) {
  return useQuery({
    queryKey: ["weather", "current", city, coords?.lat, coords?.lon],
    queryFn: async () => {
      try {
        console.log(`Fetching weather for city: ${city}`);
        const data = await weatherApi.getCurrentWeather(city, coords);
        console.log("Weather data received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to fetch weather for ${city}:`, error);
        throw error;
      }
    },
    enabled: enabled && (!!city || !!coords),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
}
