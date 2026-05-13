import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import { CloudSun, AlertCircle, Check, RefreshCw } from "lucide-react";
import { Sidebar } from "@/components/weather/Sidebar";
import { TopBar } from "@/components/weather/TopBar";
import { HeroCard } from "@/components/weather/HeroCard";
import { ForecastStrip } from "@/components/weather/ForecastStrip";
import { DetailGrid } from "@/components/weather/DetailGrid";
import { WhatToWear } from "@/components/weather/WhatToWear";
import { CompareCities } from "@/components/weather/CompareCities";
import { ChatThread } from "@/components/weather/ChatThread";
import { PromptBar } from "@/components/weather/PromptBar";
import { initialChat, type ChatMessage } from "@/components/weather/data";
import { useAutoDetect } from "@/hooks/useAutoDetect";
import { useWeather } from "@/hooks/useWeather";
import { useForecast } from "@/hooks/useForecast";
import { useWeatherDetail } from "@/hooks/useWeatherDetail";
import { useClothingAdvice } from "@/hooks/useClothingAdvice";
import { useChat } from "@/hooks/useChat";
import { useAuth } from "@/contexts/AuthContext";
import type { Condition } from "@/components/weather/data";

// Note: the 'head' property is removed as it is only for SSR.
export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  const { user } = useAuth();
  const [unit, setUnit] = useState<"C" | "F">("C");
  const [selectedDay, setSelectedDay] = useState(0);
  const [activeHistory, setActiveHistory] = useState("1");
  const [messages, setMessages] = useState<ChatMessage[]>(initialChat);
  const [mobileNav, setMobileNav] = useState(false);
  const [city, setCity] = useState<string>("London");

  // 1. Client-side Meta Tag Management
  useEffect(() => {
    document.title = "EL-Exousia Weather — AI Weather Intelligence";
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

  // 2. Data Fetching Hooks
  const { data: autoData } = useAutoDetect();
  
  useEffect(() => {
    if (autoData?.city && city === "London") {
      setCity(autoData.city);
    }
  }, [autoData, city]);

  const { data: weatherData, isLoading: weatherLoading, error: weatherError } = useWeather(city, true);
  const { data: forecastData, isLoading: forecastLoading } = useForecast(city, true, 7);
  const today = new Date().toISOString().split('T')[0];
  const { data: detailData, isLoading: detailLoading } = useWeatherDetail(city, today, true);
  const { data: clothingData } = useClothingAdvice(city, true);

  // 3. Chat functionality
  const { sendMessage, isStreaming, currentResponse, resolvedCity, clearResolvedCity } = useChat();
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  const handleCitySelect = useCallback(
    (next: string) => {
      clearResolvedCity();
      setCity(next);
    },
    [clearResolvedCity]
  );

  // Only react when the chat stream emits a *new* resolved_city. Including `city`
  // in the dependency array caused this effect to re-run after sidebar / saved /
  // search picks and overwrite the user's choice with a stale `resolvedCity`.
  useEffect(() => {
    if (!resolvedCity) return;
    setCity((prev) => (resolvedCity !== prev ? resolvedCity : prev));
  }, [resolvedCity]);

  const handleSend = async (text: string) => {
    const id = Date.now().toString();
    setMessages((m) => [...m, { id, role: "user", text, time: "now" }]);
    
    const agentId = Date.now().toString() + "_agent";
    setStreamingMessageId(agentId);
    setMessages((m) => [...m, { id: agentId, role: "agent", text: "", time: "now" }]);
    
    try {
      await sendMessage(text, undefined, city, unit);
      setStreamingMessageId(null);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((m) => [
        ...m,
        { id: Date.now().toString(), role: "agent", text: "Sorry, I encountered an error. Please try again.", time: "now" },
      ]);
      setStreamingMessageId(null);
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

  const isLoading = weatherLoading || detailLoading || forecastLoading;
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
      />

      <main className="flex-1 flex flex-col min-w-0">
        <TopBar city={weather ? `${weather.city}, ${weather.country}` : "Loading..."} unit={unit} onUnit={setUnit} onMenu={() => setMobileNav(true)} user={user} />

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
                <ForecastStrip selected={selectedDay} onSelect={setSelectedDay} unit={unit} data={forecastData} city={city} />
                <DetailGrid data={detailData} />
                <WhatToWear data={clothingData} unit={unit} />
                <CompareCities unit={unit} />
              </>
            ) : null}
            <ChatThread 
              messages={messages} 
              isTyping={isStreaming} 
              agentName="EL-Exousia Weather Agent"
              dataLocation={weatherData?.city || ""}
            />
          </div>
        </div>

        <PromptBar onSend={handleSend} isStreaming={isStreaming} currentCity={city} />
      </main>
    </div>
  );
}