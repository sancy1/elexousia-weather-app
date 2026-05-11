import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
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

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "EL-Exousia Weather — AI Weather Intelligence" },
      { name: "description", content: "Real-time weather and conversational AI forecasts for any city in the world." },
    ],
  }),
  component: Index,
});

function Index() {
  const { user } = useAuth();
  const [unit, setUnit] = useState<"C" | "F">("C");
  const [selectedDay, setSelectedDay] = useState(0);
  const [activeHistory, setActiveHistory] = useState("1");
  const [messages, setMessages] = useState<ChatMessage[]>(initialChat);
  const [isTyping, setIsTyping] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [city, setCity] = useState<string>("London"); // Local city state that can be overridden

  // Auto-detect location on load (only set if city is still default London)
  const { data: autoData, isLoading: autoLoading, error: autoError } = useAutoDetect();
  
  useEffect(() => {
    if (autoData?.city && city === "London") {
      setCity(autoData.city);
    }
  }, [autoData, city]);
  const { data: weatherData, isLoading: weatherLoading, error: weatherError } = useWeather(city, true);
  
  // Get forecast
  const { data: forecastData, isLoading: forecastLoading } = useForecast(city, true, 7);
  
  // Get weather detail - pass today's date
  const today = new Date().toISOString().split('T')[0];
  
  // Get weather detail - pass today's date
  const { data: detailData, isLoading: detailLoading } = useWeatherDetail(city, today, true);
  
  // Get clothing advice
  const { data: clothingData } = useClothingAdvice(city, true);
  
  // Chat functionality
  const { sendMessage, stopChat, isStreaming, currentResponse, resolvedCity } = useChat();
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  // Update city when resolved from chat
  useEffect(() => {
    if (resolvedCity && resolvedCity !== city) {
      console.log("Updating city from chat:", resolvedCity);
      setCity(resolvedCity);
    }
  }, [resolvedCity, city]);

  // Debug: log city changes
  useEffect(() => {
    console.log("Current city:", city);
  }, [city]);

  const handleSend = async (text: string) => {
    const id = Date.now().toString();
    setMessages((m) => [
      ...m,
      { id, role: "user", text, time: "now" },
    ]);
    
    // Add empty agent message that will be updated during streaming
    const agentId = Date.now().toString() + "_agent";
    setStreamingMessageId(agentId);
    setMessages((m) => [
      ...m,
      { id: agentId, role: "agent", text: "", time: "now" },
    ]);
    
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

  // Update the streaming message in real-time
  useEffect(() => {
    if (streamingMessageId && currentResponse) {
      console.log("Updating streaming message:", streamingMessageId, currentResponse);
      setMessages((m) =>
        m.map((msg) =>
          msg.id === streamingMessageId ? { ...msg, text: currentResponse } : msg
        )
      );
    }
  }, [currentResponse, streamingMessageId]);

  // Debug: log messages state
  useEffect(() => {
    console.log("Current messages:", messages);
  }, [messages]);

  // Map weather condition to UI condition type
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
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-[400px] w-[400px] rounded-full bg-primary-glow/8 blur-[120px]" />
      </div>

      <Sidebar
        activeId={activeHistory}
        onSelect={setActiveHistory}
        onCitySelect={setCity}
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
                  <div className="rounded-2xl bg-gradient-to-br from-destructive/10 to-destructive/5 border border-destructive/20 p-6 shadow-[0_8px_30px_-10px_var(--destructive)]">
                    <div className="h-14 w-14 rounded-full bg-destructive/15 flex items-center justify-center mx-auto mb-4">
                      <AlertCircle className="h-7 w-7 text-destructive" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">Oops! We couldn't load the weather</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Something went wrong while fetching weather data for "{city}". This could be due to a network issue or the city name might be incorrect.
                    </p>
                    <div className="space-y-2 text-left bg-background/50 rounded-lg p-3 mb-4">
                      <p className="text-xs font-medium text-foreground mb-2">Try these options:</p>
                      <ul className="text-xs text-muted-foreground space-y-1.5">
                        <li className="flex items-start gap-2">
                          <Check className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                          <span>Check the city name spelling and try again</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <Check className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                          <span>Try a different city name (e.g., "London" instead of "London, UK")</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <Check className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                          <span>Check your internet connection</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <Check className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                          <span>If the problem persists, try again in a few minutes</span>
                        </li>
                      </ul>
                    </div>
                    <button
                      onClick={() => window.location.reload()}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all shadow-[0_4px_12px_-4px_var(--primary)] hover:shadow-[0_6px_16px_-4px_var(--primary)]"
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
