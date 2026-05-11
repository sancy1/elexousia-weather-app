/**
 * Base API Client
 * Handles all HTTP requests with error handling, auth, and interceptors
 */

import { env } from "./env";

class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = env.API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, ""); // Remove trailing slash
  }

  /**
   * Build URL with query parameters
   */
  private buildUrl(endpoint: string, params?: RequestConfig["params"]): string {
    const url = `${this.baseUrl}${endpoint}`;
    
    if (!params || Object.keys(params).length === 0) {
      return url;
    }

    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });

    const queryString = searchParams.toString();
    return queryString ? `${url}?${queryString}` : url;
  }

  /**
   * Get session token from cookie (for server-side auth)
   */
  private getCredentials(): RequestInit["credentials"] {
    return "include"; // Include cookies for HTTP-only session token
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get("content-type");
    const isJson = contentType?.includes("application/json");

    if (!response.ok) {
      let errorMessage = response.statusText;
      let errorData: unknown;

      if (isJson) {
        try {
          errorData = await response.json();
          errorMessage = (errorData as { detail?: string; message?: string })?.detail || 
                        (errorData as { detail?: string; message?: string })?.message || 
                        errorMessage;
        } catch {
          // Ignore JSON parse errors
        }
      }

      throw new ApiError(response.status, errorMessage, errorData);
    }

    if (isJson) {
      return response.json();
    }

    // Return text for non-JSON responses
    return response.text() as T;
  }

  /**
   * Generic request method
   */
  private async request<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<T> {
    const { params, ...requestConfig } = config;
    const url = this.buildUrl(endpoint, params);

    const response = await fetch(url, {
      ...requestConfig,
      credentials: this.getCredentials(),
      headers: {
        "Content-Type": "application/json",
        ...requestConfig.headers,
      },
    });

    return this.handleResponse<T>(response);
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: "GET" });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: "DELETE" });
  }

  /**
   * Stream request (for SSE)
   */
  async stream(endpoint: string, data?: unknown): Promise<ReadableStream> {
    const url = this.buildUrl(endpoint);
    const response = await fetch(url, {
      method: "POST",
      credentials: this.getCredentials(),
      headers: {
        "Content-Type": "application/json",
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }

    if (!response.body) {
      throw new Error("Response body is null");
    }

    return response.body;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export { ApiError };
