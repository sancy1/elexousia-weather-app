/**
 * Weather API Client
 * Functions for weather-related API calls
 */

import type {
  AutoWeatherResponse,
  CurrentWeatherResponse,
  ForecastResponse,
  HourlyForecastResponse,
  WeatherDetailResponse,
  CompareWeatherResponse,
  ClothingAdviceResponse,
  NotificationsResponse,
  CheckNotificationsResponse,
} from "./api-types";

import { apiClient } from "./api-client";
import { env } from "./env";

interface SavedLocation {
  id: number;
  city_name: string;
  country_code: string;
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  display_order: number;
  is_default: boolean;
}

interface SearchHistoryItem {
  id: number;
  user_id: number;
  city_name: string;
  country_code: string;
  searched_at: string;
  temperature: number | null;
  condition: string | null;
}

interface SaveLocationRequest {
  city_name: string;
  country_code: string;
  label: string;
}

export const weatherApi = {
  /**
   * Auto-detect location and get weather
   */
  async autoDetect(): Promise<AutoWeatherResponse> {
    return apiClient.get<AutoWeatherResponse>("/api/weather/auto");
  },

  /**
   * Get current weather for a city
   */
  async getCurrentWeather(city: string): Promise<CurrentWeatherResponse> {
    return apiClient.get<CurrentWeatherResponse>(`/api/weather/current?city=${encodeURIComponent(city)}`);
  },

  /**
   * Get 7-day forecast for a city
   */
  async getForecast(city: string, days: number = 7): Promise<ForecastResponse> {
    return apiClient.get<ForecastResponse>(`/api/weather/forecast?city=${encodeURIComponent(city)}&days=${days}`);
  },

  /**
   * Get hourly forecast for a city
   */
  async getHourlyForecast(city: string, date: string): Promise<HourlyForecastResponse> {
    return apiClient.get<HourlyForecastResponse>(
      `/api/weather/hourly?city=${encodeURIComponent(city)}&date=${encodeURIComponent(date)}`
    );
  },

  /**
   * Get detailed weather information for a city
   */
  async getWeatherDetail(city: string, date: string): Promise<WeatherDetailResponse> {
    return apiClient.get<WeatherDetailResponse>(`/api/weather/detail?city=${encodeURIComponent(city)}&date=${encodeURIComponent(date)}`);
  },

  /**
   * Compare weather between two cities
   */
  async compareCities(city1: string, city2: string): Promise<CompareWeatherResponse> {
    return apiClient.get<CompareWeatherResponse>(`/api/weather/compare?city1=${encodeURIComponent(city1)}&city2=${encodeURIComponent(city2)}`);
  },

  /**
   * Get clothing advice for a city
   */
  async getClothingAdvice(city: string): Promise<ClothingAdviceResponse> {
    return apiClient.get<ClothingAdviceResponse>(`/api/weather/wear?city=${encodeURIComponent(city)}`);
  },

  /**
   * Send chat message with SSE streaming
   */
  async chatStream(message: string, sessionId?: string, cityContext?: string, unit: string = "C"): Promise<ReadableStream> {
    const apiUrl = `${env.API_BASE_URL}/api/chat`;
    console.log(`Chat API URL: ${apiUrl}`);
    console.log(`Sending chat:`, { message, sessionId, cityContext, unit });
    
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        city_context: cityContext,
        unit,
      }),
    });

    console.log(`Chat response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Chat error response: ${errorText}`);
      throw new Error(`Chat request failed: ${response.statusText} (${response.status}) - ${errorText}`);
    }

    return response.body!;
  },

  /**
   * Get saved locations
   */
  async getSavedLocations(): Promise<{ locations: SavedLocation[] }> {
    return apiClient.get<{ locations: SavedLocation[] }>("/api/saved-locations");
  },

  /**
   * Save a location
   */

  /**
   * Get search history
   */
  async getSearchHistory(): Promise<SearchHistoryItem[]> {
    return apiClient.get<SearchHistoryItem[]>("/api/search-history");
  },

  /**
   * Add to search history
   */
  async addSearchHistory(request: {
    city_name: string;
    country_code: string;
    temperature?: number;
    condition?: string;
  }): Promise<SearchHistoryItem> {
    return apiClient.post<SearchHistoryItem>("/api/search-history", request);
  },

  /**
   * Delete search history item
   */
  async deleteSearchHistory(historyId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/api/search-history/${historyId}`);
  },

  /**
   * Clear all search history
   */
  async clearSearchHistory(): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>("/api/search-history");
  },
  async saveLocation(request: SaveLocationRequest): Promise<SavedLocation> {
    return apiClient.post<SavedLocation>("/api/saved-locations", request);
  },

  /**
   * Delete a saved location
   */
  async deleteLocation(locationId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/api/saved-locations/${locationId}`);
  },

  /**
   * Get notifications for the current user
   */
  async getNotifications(): Promise<NotificationsResponse> {
    return apiClient.get<NotificationsResponse>("/api/notifications");
  },

  /**
   * Mark notification as read
   */
  async markNotificationAsRead(notificationId: number): Promise<{ message: string }> {
    return apiClient.patch<{ message: string }>(`/api/notifications/${notificationId}/read`, {});
  },

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsAsRead(): Promise<{ message: string }> {
    return apiClient.patch<{ message: string }>("/api/notifications/read-all", {});
  },

  /**
   * Delete notification
   */
  async deleteNotification(notificationId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/api/notifications/${notificationId}`);
  },

  /**
   * Delete all notifications
   */
  async deleteAllNotifications(): Promise<{ message: string; deleted_count: number }> {
    return apiClient.delete<{ message: string; deleted_count: number }>("/api/notifications/delete-all");
  },

  /**
   * Check for new notifications
   */
  async checkNotifications(): Promise<CheckNotificationsResponse> {
    return apiClient.post<CheckNotificationsResponse>("/api/notifications/check", {});
  },
};
