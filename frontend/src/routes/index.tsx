import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useCallback } from "react";
import { CloudSun, AlertCircle, Check, RefreshCw } from "lucide-react";
import { Sidebar } from "@/components/weather/Sidebar";
import { TopBar } from "@/components/weather/TopBar";
import { HeroCard } from "@/components/weather/HeroCard";
import { DetailGrid } from "@/components/weather/DetailGrid";
import { WhatToWear } from "@/components/weather/WhatToWear";
import { CompareCities } from "@/components/weather/CompareCities";
import { ChatThread } from "@/components/weather/ChatThread";
import { PromptBar } from "@/components/weather/PromptBar";
import { initialChat, type ChatMessage } from "@/components/weather/data";
import { useLocationResolution } from "@/hooks/useLocationResolution";
import { useWeather } from "@/hooks/useWeather";
import { useWeatherDetail } from "@/hooks/useWeatherDetail";
import { useClothingAdvice } from "@/hooks/useClothingAdvice";
import { useChat } from "@/hooks/useChat";
import { useAuth } from "@/contexts/AuthContext";
import { chatHistoryApi, optimisticAddConversation } from "@/lib/chat-history";
import type { ConversationSummary } from "@/lib/api-types";
import type { Condition } from "@/components/weather/data";

// Note: the 'head' property is removed as it is only for SSR.
export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [unit, setUnit] = useState<"C" | "F">("C");
  const [activeHistory, setActiveHistory] = useState("1");
  const [messages, setMessages] = useState<ChatMessage[]>(initialChat);
  const [mobileNav, setMobileNav] = useState(false);
  const {
    city,
    locationStatus,
    coords,
    locationLabel,
    geoLoading,
    geoError,
    handleLocate,
    selectCity,
  } = useLocationResolution();
  const [sessionId, setSessionId] = useState<string>("");

  // Persistent chat session id for conversation memory (survives reloads).
  useEffect(() => {
    try {
      const key = "elexousia_chat_session_id";
      let id = window.localStorage.getItem(key);
      if (!id) {
        id =
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        window.localStorage.setItem(key, id);
      }
      setSessionId(id);
    } catch {
      // localStorage unavailable — chat still works without memory
      setSessionId("");
    }
  }, []);

  // 1. Client-side Meta Tag Management
  useEffect(() => {
    document.title = "Elexousia Weather — AI Weather Intelligence";
    const metaDesc = document.querySelector('meta[name="description"]');
    const content = "Real-time weather and conversational AI forecasts for any city in the world.";
    
    if (metaDesc) {
      metaDesc.setAttribute("content", content);
    } else {
      const meta = document.createElement('meta');
      meta.name = "description";
      meta.content = content;
      document.head.appendChild(meta);
    }
  }, []);

  // 2. Data Fetching Hooks — gated on resolved location (empty city = no fetch)
  const { data: weatherData, isLoading: weatherLoading, error: weatherError } = useWeather(city, true, coords ?? undefined);
  const today = new Date().toISOString().split('T')[0];
  const { data: detailData, isLoading: detailLoading } = useWeatherDetail(city, today, true, coords ?? undefined);
  const { data: clothingData } = useClothingAdvice(city, true, coords ?? undefined);

  // 3. Chat functionality
  const { sendMessage, isStreaming, currentResponse, resolvedCity, clearResolvedCity } = useChat();
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  const handleCitySelect = useCallback(
    (next: string) => {
      clearResolvedCity();
      selectCity(next);
    },
    [clearResolvedCity, selectCity]
  );

  // Only react when the chat stream emits a *new* resolved_city. Including `city`
  // in the dependency array caused this effect to re-run after sidebar / saved /
  // search picks and overwrite the user's choice with a stale `resolvedCity`.
  useEffect(() => {
    if (!resolvedCity) return;
    selectCity(resolvedCity);
  }, [resolvedCity, selectCity]);

  const scrollToChat = useCallback(() => {
    // Let React render the loaded messages, then bring the chat into view.
    requestAnimationFrame(() => {
      setTimeout(() => {
        document
          .getElementById("chat-thread")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    });
  }, []);

  // Load a past conversation into the chat area and continue its session.
  const handleLoadConversation = useCallback(
    async (conv: ConversationSummary) => {
      try {
        const { messages: exchanges } = await chatHistoryApi.getMessages(
          conv.id,
          sessionId || undefined
        );
        const loaded: ChatMessage[] = [];
        exchanges.forEach((ex, i) => {
          if (ex.user_message) {
            loaded.push({ id: `h${i}u`, role: "user", text: ex.user_message, time: "" });
          }
          if (ex.bot_response) {
            loaded.push({ id: `h${i}a`, role: "agent", text: ex.bot_response, time: "" });
          }
        });
        setMessages(loaded.length ? loaded : initialChat);
        // Continue the loaded conversation's session so new messages
        // are appended to it rather than the previous session.
        setSessionId(conv.session_id);
        try {
          window.localStorage.setItem("elexousia_chat_session_id", conv.session_id);
        } catch { /* ignore */ }
        if (conv.city_name) {
          selectCity(conv.city_name);
        }
        clearResolvedCity();
        scrollToChat();
      } catch {
        // Leave current chat untouched on failure
      }
    },
    [sessionId, clearResolvedCity, selectCity, scrollToChat]
  );

  // Start a fresh conversation with a new session id.
  const handleNewChat = useCallback(() => {
    const id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setSessionId(id);
    try {
      window.localStorage.setItem("elexousia_chat_session_id", id);
    } catch { /* ignore */ }
    setMessages(initialChat);
    clearResolvedCity();
    scrollToChat();
  }, [clearResolvedCity, scrollToChat]);

  // If the deleted conversation is the one currently open (or history was
  // cleared), start a fresh chat so the UI never shows a dead session.
  const handleConversationDeleted = useCallback(
    (conv: ConversationSummary) => {
      if (conv.id === -1 || conv.session_id === sessionId) {
        handleNewChat();
      }
    },
    [sessionId, handleNewChat]
  );

  const handleSend = async (text: string) => {
    const id = Date.now().toString();
    setMessages((m) => [...m, { id, role: "user", text, time: "now" }]);

    // Optimistically surface this session in Chat History the moment the
    // first message is accepted — the backend only creates the conversation
    // row after the response completes, so without this the entry would not
    // appear until a refresh. A negative temp id is replaced by the real row
    // on the post-response invalidation below.
    if (sessionId) {
      optimisticAddConversation(queryClient, sessionId, text, locationLabel || city || null);
    }

    const agentId = Date.now().toString() + "_agent";
    setStreamingMessageId(agentId);
    setMessages((m) => [...m, { id: agentId, role: "agent", text: "", time: "now" }]);
    
    try {
      const finalText = await sendMessage(text, sessionId || undefined, locationLabel || city, unit);
      const displayText = finalText && finalText.trim()
        ? finalText
        : "I'm sorry, I didn't receive a response from the weather agent. Please try asking again — for example, 'What's the weather in London?'";
      setMessages((m) =>
        m.map((msg) =>
          msg.id === agentId ? { ...msg, text: displayText } : msg
        )
      );
      setStreamingMessageId(null);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((m) =>
        m.map((msg) =>
          msg.id === agentId
            ? { ...msg, text: "Sorry, I encountered an error. Please try again." }
            : msg
        )
      );
      setStreamingMessageId(null);
    } finally {
      // Reconcile optimistic history entry with the real conversation row
      // (created server-side once the exchange is persisted).
      queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
    }
  };

  useEffect(() => {
    if (streamingMessageId && currentResponse) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === streamingMessageId ? { ...msg, text: currentResponse } : msg
        )
      );
    }
  }, [currentResponse, streamingMessageId]);

  const mapCondition = (condition: string): Condition => {
    const lower = condition.toLowerCase();
    if (lower.includes("rain") || lower.includes("shower")) return "rainy";
    if (lower.includes("drizzle")) return "drizzle";
    if (lower.includes("cloud") || lower.includes("overcast")) return "cloudy";
    if (lower.includes("partly") || lower.includes("partial")) return "partly";
    if (lower.includes("fog") || lower.includes("mist")) return "fog";
    if (lower.includes("snow")) return "snow";
    if (lower.includes("sun") || lower.includes("clear")) return "sunny";
    return "sunny";
  };

  const isLoading =
    locationStatus === "initializing" || weatherLoading || detailLoading;
  const error = weatherError;
  const weather = weatherData;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-[400px] w-[400px] rounded-full bg-primary-glow/8 blur-[120px]" />
      </div>

      <Sidebar
        activeId={activeHistory}
        onSelect={setActiveHistory}
        onCitySelect={handleCitySelect}
        mobileOpen={mobileNav}
        onMobileClose={() => setMobileNav(false)}
        currentCity={city}
        sessionId={sessionId || undefined}
        onLoadConversation={handleLoadConversation}
        onNewChat={handleNewChat}
        onConversationDeleted={handleConversationDeleted}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <TopBar
          city={
            locationStatus === "initializing"
              ? "Detecting location…"
              : locationStatus === "needs_manual"
                ? "Choose your location"
                : locationLabel ||
                  (weather ? `${weather.city}, ${weather.country}` : city || "…")
          }
          unit={unit}
          onUnit={setUnit}
          onMenu={() => setMobileNav(true)}
          user={user}
          onLocate={handleLocate}
          locating={geoLoading}
          locationError={geoError}
          approximate={locationStatus === "resolved_approximate"}
        />

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="w-full max-w-[1100px] mx-auto px-4 sm:px-6 py-6 space-y-6 transition-all">
            {isLoading ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4 animate-pulse">
                    <CloudSun className="h-6 w-6 text-primary" />
                  </div>
                  <p className="text-foreground font-medium">Loading weather data...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center py-12 px-4">
                <div className="max-w-md w-full text-center">
                  <div className="rounded-2xl bg-gradient-to-br from-destructive/10 to-destructive/5 border border-destructive/20 p-6 shadow-lg">
                    <div className="h-14 w-14 rounded-full bg-destructive/15 flex items-center justify-center mx-auto mb-4">
                      <AlertCircle className="h-7 w-7 text-destructive" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">Oops! We couldn't load the weather</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Something went wrong while fetching data for "{city}".
                    </p>
                    <button
                      onClick={() => window.location.reload()}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all"
                    >
                      <RefreshCw className="h-4 w-4" />
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            ) : locationStatus === "needs_manual" ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-center max-w-sm">
                  <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <CloudSun className="h-7 w-7 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">Where are you?</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    We couldn't detect your location automatically. Search for your city in the sidebar,
                    or tap the location button for precise weather.
                  </p>
                </div>
              </div>
            ) : weather ? (
              <>
                <HeroCard
                  city={weather.city}
                  country={weather.country}
                  time={weather.local_time}
                  temp={unit === "C" ? weather.temperature_c : weather.temperature_f}
                  feels={unit === "C" ? weather.feels_like_c : weather.feels_like_f}
                  condition={mapCondition(weather.condition)}
                  unit={unit}
                  humidity={weather.humidity_pct}
                  windKph={weather.wind_kph}
                  windDirection={weather.wind_direction}
                  uvIndex={weather.uv_index}
                  visibilityKm={weather.visibility_km}
                />
                <DetailGrid data={detailData} />
                <WhatToWear data={clothingData} unit={unit} />
                <CompareCities unit={unit} />
              </>
            ) : null}
            <div id="chat-thread">
              <ChatThread 
                messages={messages} 
                isTyping={isStreaming} 
                agentName="Elexousia Weather Agent"
                dataLocation={weatherData?.city || ""}
              />
            </div>
          </div>
        </div>

        <PromptBar onSend={handleSend} isStreaming={isStreaming} currentCity={city} />
      </main>
    </div>
  );
}