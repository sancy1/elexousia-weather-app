import type { LucideIcon } from "lucide-react";
import { Cloud, CloudRain, CloudSun, Sun, CloudDrizzle, CloudFog, CloudSnow } from "lucide-react";

export type Condition = "sunny" | "cloudy" | "rainy" | "partly" | "drizzle" | "fog" | "snow";

export const conditionIcon: Record<Condition, LucideIcon> = {
  sunny: Sun,
  cloudy: Cloud,
  rainy: CloudRain,
  partly: CloudSun,
  drizzle: CloudDrizzle,
  fog: CloudFog,
  snow: CloudSnow,
};

export const conditionLabel: Record<Condition, string> = {
  sunny: "Clear sky",
  cloudy: "Cloudy",
  rainy: "Patchy rain nearby",
  partly: "Partly cloudy",
  drizzle: "Light drizzle",
  fog: "Misty",
  snow: "Light snow",
};

export type DayForecast = {
  day: string;
  condition: Condition;
  high: number;
  low: number;
  rain: number;
};

export const weekForecast: DayForecast[] = [
  { day: "Today", condition: "rainy", high: 30, low: 24, rain: 65 },
  { day: "Sun", condition: "partly", high: 31, low: 25, rain: 40 },
  { day: "Mon", condition: "rainy", high: 29, low: 23, rain: 80 },
  { day: "Tue", condition: "partly", high: 32, low: 26, rain: 15 },
  { day: "Wed", condition: "sunny", high: 33, low: 27, rain: 5 },
  { day: "Thu", condition: "partly", high: 30, low: 24, rain: 30 },
  { day: "Fri", condition: "rainy", high: 28, low: 23, rain: 55 },
];

export type SearchHistoryItem = {
  id: string;
  city: string;
  when: string;
  temp: number;
  condition: string;
};

export const searchHistory: SearchHistoryItem[] = [
  { id: "1", city: "Lagos, Nigeria", when: "Today", temp: 28, condition: "Rainy" },
  { id: "2", city: "London, UK", when: "Yesterday", temp: 14, condition: "Cloudy" },
  { id: "3", city: "New York, US", when: "2 days ago", temp: 18, condition: "Clear" },
  { id: "4", city: "Dubai, UAE", when: "3 days ago", temp: 38, condition: "Sunny" },
  { id: "5", city: "Tokyo, Japan", when: "4 days ago", temp: 22, condition: "Partly cloudy" },
  { id: "6", city: "Paris, France", when: "5 days ago", temp: 16, condition: "Overcast" },
];

export const savedLocations = [
  { id: "a", city: "Abuja, Nigeria", label: "Home" },
  { id: "b", city: "Accra, Ghana", label: "Work" },
  { id: "c", city: "Cape Town, ZA", label: "Travel" },
];

export const quickChips: { label: string; icon: string }[] = [
  { label: "3-day forecast", icon: "📅" },
  { label: "7-day forecast", icon: "📆" },
  { label: "Compare with another city", icon: "⚖️" },
  { label: "Travel advice", icon: "✈️" },
  { label: "What to wear", icon: "👕" },
  { label: "Rain probability this week", icon: "☂️" },
  { label: "Best day to travel", icon: "🗓️" },
];

export type ChatMessage =
  | { id: string; role: "user"; text: string; time: string }
  | { id: string; role: "agent"; text: string; time: string };

export const initialChat: ChatMessage[] = [];