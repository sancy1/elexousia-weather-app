/**
 * useWeatherDetail Hook
 * Custom hook for fetching weather detail data
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/weather";
import type { WeatherDetailResponse } from "@/lib/api-types";

export function useWeatherDetail(city: string, date: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["weather", "detail", city, date],
    queryFn: async () => {
      try {
        console.log(`Fetching weather detail for city: ${city}, date: ${date}`);
        const data = await weatherApi.getWeatherDetail(city, date);
        console.log("Weather detail received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to fetch weather detail for ${city}:`, error);
        // Return empty data on error to prevent UI from breaking
        return {
          city: city,
          date: date,
          rain: { chance_pct: 0, total_mm: 0, will_it_rain: false },
          pressure: { hpa: 1013 },
          uv: { index: 0, level: "Low" },
          sun: { sunrise: "N/A", sunset: "N/A", moonrise: "N/A", moonset: "N/A", moon_phase: "N/A" },
          condition: { text: "Unknown", icon: "" }
        } as WeatherDetailResponse;
      }
    },
    enabled: enabled && !!city && !!date,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 0,
  });
}
