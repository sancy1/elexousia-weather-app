import { useState } from "react";
import { conditionIcon } from "./data";
import type { ForecastResponse } from "@/lib/api-types";
import { useHourlyForecast } from "@/hooks/useHourlyForecast";

interface Props {
  selected: number;
  onSelect: (i: number) => void;
  unit: "C" | "F";
  data?: ForecastResponse;
  city?: string;
}

const conv = (c: number, u: "C" | "F") => (u === "C" ? c : Math.round((c * 9) / 5 + 32));

function mapCondition(condition: string): "sunny" | "rainy" | "cloudy" | "partly" | "drizzle" | "fog" | "snow" {
  const lower = condition.toLowerCase();
  if (lower.includes("rain") || lower.includes("shower")) return "rainy";
  if (lower.includes("drizzle")) return "drizzle";
  if (lower.includes("cloud") || lower.includes("overcast")) return "cloudy";
  if (lower.includes("partly") || lower.includes("partial")) return "partly";
  if (lower.includes("fog") || lower.includes("mist")) return "fog";
  if (lower.includes("snow")) return "snow";
  if (lower.includes("sun") || lower.includes("clear")) return "sunny";
  return "sunny";
}

export function ForecastStrip({ selected, onSelect, unit, data, city }: Props) {
  const [viewMode, setViewMode] = useState<"days" | "hours">("days");
  
  // Get the selected date for hourly forecast
  const selectedDate = data?.forecast?.[selected]?.date || new Date().toISOString().split('T')[0];
  
  const { data: hourlyData, isLoading: hourlyLoading } = useHourlyForecast(
    city || "",
    selectedDate,
    viewMode === "hours" && !!city
  );

  if (!data || !data.forecast) {
    return null;
  }

  const handleViewModeChange = (mode: "days" | "hours") => {
    setViewMode(mode);
  };

  // Render hourly forecast view
  if (viewMode === "hours" && hourlyData?.hourly) {
    const hoursToShow = hourlyData.hourly.slice(0, 12); // Show first 12 hours
    
    return (
      <div className="animate-slide-up" style={{ animationDelay: "80ms" }}>
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-[10px] font-semibold tracking-[0.14em] uppercase text-muted-foreground">
            Hourly Forecast - {selectedDate}
          </span>
          <div className="flex items-center bg-secondary border border-border rounded-md p-0.5">
            {["Days", "Hours"].map((t, i) => (
              <button
                key={t}
                onClick={() => handleViewModeChange(i === 0 ? "days" : "hours")}
                className={`text-[10px] font-medium px-2.5 py-1 rounded transition-colors ${
                  i === 1 ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        {hourlyLoading ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            Loading hourly data...
          </div>
        ) : (
          <div className="grid grid-cols-6 sm:grid-cols-12 gap-2">
            {hoursToShow.map((hour, i) => {
              const condition = mapCondition(hour.condition);
              const Icon = conditionIcon[condition];
              const time = new Date(hour.time);
              const hourStr = time.toLocaleTimeString("en-US", { hour: "numeric", hour12: true });
              
              return (
                <div
                  key={i}
                  className="group rounded-xl p-2 border bg-card/60 border-border text-center"
                >
                  <div className="text-[10px] text-muted-foreground mb-1">
                    {hourStr}
                  </div>
                  <div className="flex justify-center my-1">
                    <Icon
                      className={`h-5 w-5 ${
                        condition === "sunny"
                          ? "text-sun"
                          : condition === "rainy"
                          ? "text-rain"
                          : "text-sky"
                      }`}
                      strokeWidth={1.8}
                    />
                  </div>
                  <div className="text-[13px] font-semibold">
                    {conv(unit === "C" ? hour.temperature_c : hour.temperature_f, unit)}°
                  </div>
                  <div className="text-[9px] text-muted-foreground mt-0.5">
                    {hour.rain_chance_pct}%
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="animate-slide-up" style={{ animationDelay: "80ms" }}>
      <div className="flex items-center justify-between mb-3 px-1">
        <span className="text-[10px] font-semibold tracking-[0.14em] uppercase text-muted-foreground">
          7-Day Forecast
        </span>
        <div className="flex items-center bg-secondary border border-border rounded-md p-0.5">
          {["Days", "Hours"].map((t, i) => (
            <button
              key={t}
              onClick={() => handleViewModeChange(i === 0 ? "days" : "hours")}
              className={`text-[10px] font-medium px-2.5 py-1 rounded transition-colors ${
                i === 0 ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-7 gap-2">
        {data.forecast.map((d, i) => {
          const condition = mapCondition(d.condition);
          const Icon = conditionIcon[condition];
          const active = i === selected;
          const dayName = d.day_name || new Date(d.date).toLocaleDateString("en-US", { weekday: "short" });
          return (
            <button
              key={d.date}
              onClick={() => onSelect(i)}
              className={`group relative rounded-xl p-3 border transition-all ${
                active
                  ? "bg-accent/80 border-primary/60 shadow-[0_0_0_1px_var(--primary)/30,0_8px_24px_-12px_var(--primary)]"
                  : "bg-card/60 border-border hover:bg-accent/40 hover:border-border"
              }`}
            >
              <div className={`text-[11px] font-semibold ${active ? "text-primary-glow" : "text-muted-foreground"}`}>
                {dayName}
              </div>
              <div className="my-2 flex justify-center">
                <Icon
                  className={`h-7 w-7 ${
                    condition === "sunny"
                      ? "text-sun"
                      : condition === "rainy"
                      ? "text-rain"
                      : "text-sky"
                  } ${active ? "animate-float" : ""}`}
                  strokeWidth={1.8}
                />
              </div>
              <div className="text-center">
                <div className="text-[15px] font-semibold leading-tight">{conv(unit === "C" ? d.high_c : d.high_f, unit)}°</div>
                <div className="text-[11px] text-muted-foreground leading-tight">{conv(unit === "C" ? d.low_c : d.low_f, unit)}°</div>
              </div>
              <div className={`mt-1.5 text-center text-[10px] font-semibold ${active ? "text-primary-glow" : "text-sky"}`}>
                {d.rain_chance_pct}%
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
