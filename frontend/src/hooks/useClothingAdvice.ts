/**
 * useClothingAdvice Hook
 * Custom hook for fetching clothing advice
 */

import { useQuery } from "@tanstack/react-query";
import { weatherApi, type Coords } from "@/lib/weather";
import type { ClothingAdviceResponse } from "@/lib/api-types";

export function useClothingAdvice(city: string, enabled: boolean = true, coords?: Coords) {
  return useQuery({
    queryKey: ["weather", "clothing", city, coords?.lat, coords?.lon],
    queryFn: async () => {
      try {
        console.log(`Fetching clothing advice for city: ${city}`);
        const data = await weatherApi.getClothingAdvice(city, coords);
        console.log("Clothing advice received:", data);
        return data;
      } catch (error) {
        console.error(`Failed to fetch clothing advice for ${city}:`, error);
        throw error;
      }
    },
    enabled: enabled && (!!city || !!coords),
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    retry: 1,
  });
}
