/**
 * useChat Hook
 * Custom hook for AI chat with SSE streaming
 */

import { useState, useCallback, useRef } from "react";
import { weatherApi } from "@/lib/weather";

export interface ChatEvent {
  type: "start" | "token" | "done" | "error" | "resolved_city";
  content?: string;
  detail?: string;
  session_id?: string | null;
  city?: string;
}

// Convert backend errors into friendly user-facing messages
function formatErrorMessage(errorDetail: string): string {
  const detail = errorDetail.toLowerCase();
  
  // Handle tool call validation errors (e.g., days as string instead of int)
  if (detail.includes("tool call validation failed") || detail.includes("parameters for tool")) {
    return "There was a technical issue processing your request. Please try asking differently, such as 'Show me the 3-day forecast for London'.";
  }
  
  // Handle city resolution errors
  if (detail.includes("cannot resolve") || detail.includes("city") && detail.includes("not found")) {
    return "I couldn't find that city. Please try a different city name or include the country.";
  }
  
  // Handle weather data fetch errors
  if (detail.includes("failed to fetch weather") || detail.includes("weather data")) {
    return "I'm having trouble fetching weather data. Please try again in a moment.";
  }
  
  // Handle rate limiting or API errors
  if (detail.includes("rate") || detail.includes("quota") || detail.includes("too many")) {
    return "The service is temporarily busy. Please wait a moment and try again.";
  }
  
  // Generic error fallback
  return "Something went wrong with your request. Please try again.";
}

// Remove tool-specific tags and code fences that may appear in tool outputs
function sanitizeText(s: string): string {
  if (!s) return s;
  let out = s;
  // Remove tags like <|python_tag|>
  out = out.replace(/<\|[^|>]+?\|>/g, "");
  // Remove fenced code block markers like ```python
  out = out.replace(/```[a-zA-Z0-9_-]*\n?/g, "");
  // Remove any remaining triple backticks
  out = out.replace(/```/g, "");
  // Normalize unicode spaces (narrow no-break U+202F, no-break U+00A0) to regular spaces
  out = out.replace(/[  ]/g, " ");
  // Trim extra whitespace
  return out.trim();
}

export function useChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [resolvedCity, setResolvedCity] = useState<string | null>(null);
  const [currentResponse, setCurrentResponse] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);
  const responseRef = useRef("");

  const sendMessage = useCallback(
    async (message: string, sessionId?: string, cityContext?: string, unit: string = "C") => {
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      setIsStreaming(true);
      setCurrentResponse("");
      responseRef.current = "";
      abortControllerRef.current = new AbortController();

      try {
        console.log(`Sending chat message: ${message}`);
        const stream = await weatherApi.chatStream(message, sessionId, cityContext, unit);

        const reader = stream.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const event: ChatEvent = JSON.parse(line.slice(6));
                console.log("Chat event received:", event);

                if (event.type === "resolved_city" && event.city) {
                  setResolvedCity(event.city);
                } else if (event.type === "token" && event.content) {
                  const sanitized = sanitizeText(event.content || "");
                  responseRef.current += sanitized;
                  setCurrentResponse(responseRef.current);
                } else if (event.type === "done") {
                  setIsStreaming(false);
                } else if (event.type === "error") {
                  console.error("Chat error:", event.detail);
                  const friendlyMessage = formatErrorMessage(sanitizeText(event.detail || "Unknown error"));
                  responseRef.current += `\n\n${friendlyMessage}`;
                  setCurrentResponse(responseRef.current);
                  setIsStreaming(false);
                }
              } catch (e) {
                console.error("Failed to parse chat event:", e);
              }
            }
          }
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.error("Chat streaming error:", error);
          const fallback = "Sorry, I encountered an error. Please try again.";
          responseRef.current = fallback;
          setCurrentResponse(fallback);
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }

      return responseRef.current;
    },
    []
  );

  const stopChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  const clearResolvedCity = useCallback(() => {
    setResolvedCity(null);
  }, []);

  return {
    resolvedCity,
    clearResolvedCity,
    sendMessage,
    stopChat,
    isStreaming,
    currentResponse,
  };
}
