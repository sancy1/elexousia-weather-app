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

export function useChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [resolvedCity, setResolvedCity] = useState<string | null>(null);
  const [currentResponse, setCurrentResponse] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (message: string, sessionId?: string, cityContext?: string, unit: string = "C") => {
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      setIsStreaming(true);
      setCurrentResponse("");
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
                  setCurrentResponse((prev) => prev + event.content);
                } else if (event.type === "done") {
                  setIsStreaming(false);
                } else if (event.type === "error") {
                  console.error("Chat error:", event.detail);
                  setCurrentResponse((prev) => prev + `\n\nError: ${event.detail}`);
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
          setCurrentResponse("Sorry, I encountered an error. Please try again.");
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }

      return currentResponse;
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
