/**
 * API Types
 * TypeScript interfaces for all API requests and responses
 * Based on backend FastAPI schemas
 */

// ============================================================
// AUTH TYPES
// ============================================================

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  avatar_url: string | null;
  initials: string;
  unit_preference: "C" | "F";
  theme: string;
  provider: "google" | "github";
  created_at: string;
}

export interface PreferencesUpdate {
  unit_preference?: "C" | "F";
  theme?: string;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

export interface DebugTokenResponse {
  session_token: string | null;
  user_id: number;
  email: string;
  note: string;
}

// ============================================================
// WEATHER TYPES
// ============================================================

export interface AutoWeatherResponse {
  city: string;
  country: string;
  country_code: string;
  local_time: string;
  temperature_c: number;
  temperature_f: number;
  feels_like_c: number;
  feels_like_f: number;
  condition: string;
  humidity_pct: number;
  wind_kph: number;
  wind_direction: string;
  uv_index: number;
  visibility_km: number;
  cloud_cover_pct: number;
  pressure_hpa: number;
  sunrise: string;
  sunset: string;
  forecast: WeatherForecastDay[];
  advice: string;
}

export interface CurrentWeatherResponse {
  city: string;
  country: string;
  country_code: string;
  local_time: string;
  temperature_c: number;
  temperature_f: number;
  feels_like_c: number;
  feels_like_f: number;
  condition: string;
  humidity_pct: number;
  wind_kph: number;
  wind_direction: string;
  uv_index: number;
  visibility_km: number;
  cloud_cover_pct: number;
  pressure_hpa: number;
}

export interface WeatherForecastDay {
  date: string;
  day_name?: string;
  high_c: number;
  low_c: number;
  high_f: number;
  low_f: number;
  condition: string;
  rain_chance_pct: number;
  total_rain_mm?: number;
  humidity_pct: number;
  uv_index: number;
  sunrise: string;
  sunset: string;
}

export interface ForecastResponse {
  city: string;
  country: string;
  days_requested: number;
  forecast: WeatherForecastDay[];
}

export interface CompareWeatherResponse {
  city_1: CityWeatherData;
  city_2: CityWeatherData;
  comparison: {
    warmer_city: string;
    cooler_city: string;
    temp_difference_c: number;
    temp_difference_f: number;
  };
}

export interface CityWeatherData {
  city: string;
  country: string;
  temperature_c: number;
  temperature_f: number;
  feels_like_c: number;
  condition: string;
  humidity_pct: number;
  wind_kph: number;
  uv_index: number;
}

export interface HourlyForecastResponse {
  city: string;
  date: string;
  hourly: HourlyData[];
}

export interface HourlyData {
  time: string;
  temperature_c: number;
  temperature_f: number;
  condition: string;
  humidity_pct: number;
  wind_kph: number;
  wind_direction: string;
  rain_chance_pct: number;
  uv_index: number;
}

export interface WeatherDetailResponse {
  city: string;
  date: string;
  rain: {
    chance_pct: number;
    total_mm: number;
    will_it_rain: boolean;
  };
  pressure: {
    hpa: number;
  };
  uv: {
    index: number;
    level: string;
  };
  sun: {
    sunrise: string;
    sunset: string;
    moonrise: string;
    moonset: string;
    moon_phase: string;
  };
  condition: {
    text: string;
    icon: string;
  };
}

export interface ClothingAdviceResponse {
  city: string;
  country: string;
  temperature_c: number;
  temperature_f: number;
  condition: string;
  emoji: string;
  summary: string;
  tagline: string;
  items: ClothingItem[];
  tip: string;
  date?: string;
  occasion?: string;
}

export interface ClothingItem {
  icon: string;
  name: string;
  note: string;
}

export interface ClothingAdviceRequest {
  city: string;
  date?: string; // YYYY-MM-DD
  occasion?: "general" | "work" | "casual" | "formal" | "outdoor";
}

// ============================================================
// CHAT TYPES
// ============================================================

export interface ChatRequest {
  message: string;
  session_id?: string;
  city_context?: string;
  unit: "C" | "F";
}

export interface ChatEvent {
  type: "content" | "error" | "done" | "tool_call";
  content?: string;
  detail?: string;
  tool_name?: string;
  tool_result?: string;
}

export interface StopChatResponse {
  success: boolean;
  message: string;
}

// ============================================================
// CHIPS TYPES
// ============================================================

export interface Chip {
  id: number;
  label: string;
  prompt_text: string;
  icon: string;
  requires_city: boolean;
}

export interface ChipsResponse {
  chips: Chip[];
}

// ============================================================
// SAVED LOCATIONS TYPES
// ============================================================

export interface SavedLocation {
  id: number;
  user_id: number;
  city_name: string;
  country_code: string;
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  is_default: boolean;
  display_order: number;
  created_at: string;
}

export interface SavedLocationsResponse {
  locations: SavedLocation[];
}

export interface SaveLocationRequest {
  city_name: string;
  country_code: string;
  label: string;
}

export interface UpdateLocationRequest {
  label?: string;
  display_order?: number;
}

// ============================================================
// CONVERSATIONS TYPES
// ============================================================

export interface Conversation {
  id: number;
  user_id: number;
  session_id: string;
  title: string | null;
  city_name: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
  page: number;
  per_page: number;
}

export interface CreateConversationRequest {
  session_id: string;
  title?: string;
  city_name?: string;
}

export interface UpdateConversationRequest {
  title?: string;
  is_archived?: boolean;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface MessagesResponse {
  messages: Message[];
  total: number;
  page: number;
  per_page: number;
}

// ============================================================
// SEARCH TYPES
// ============================================================

export interface SearchResult {
  type: "saved_location" | "conversation" | "city";
  id: number;
  display: string;
  secondary: string | null;
  rank: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export interface CitySearchResult {
  id: number;
  city_name: string;
  country_name: string;
  country_code: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface CitySearchResponse {
  cities: CitySearchResult[];
  total: number;
  query: string;
}

// ============================================================
// NOTIFICATIONS TYPES
// ============================================================

export interface Notification {
  id: number;
  user_id: number;
  type: "rain_alert" | "heat_alert" | "cold_alert" | "info";
  city_name: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  unread_count: number;
  notifications: Notification[];
}

export interface CheckNotificationsResponse {
  message: string;
  notifications_created: number;
}

// ============================================================
// HEALTH TYPES
// ============================================================

export interface HealthResponse {
  status: "healthy" | "degraded" | "error";
  service: string;
  version: string;
  uptime_seconds: number;
  timestamp: string;
}

export interface DatabaseHealthResponse {
  status: "connected" | "disconnected";
  database?: string;
  latency_ms: number;
  server_time?: string;
  attempt?: number;
  error?: string;
  attempts?: number;
}

export interface AgentHealthResponse {
  status: "healthy" | "degraded";
  ollama: {
    status: "connected" | "unavailable";
    url: string;
    models_available?: number;
    default_model: string;
    model_available?: boolean;
    error?: string;
  };
}
