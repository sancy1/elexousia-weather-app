import { CloudRain, Sunrise, Gauge, Cloud, TrendingUp } from "lucide-react";
import type { WeatherDetailResponse } from "@/lib/api-types";

interface Props {
  data?: WeatherDetailResponse;
}

export function DetailGrid({ data }: Props) {
  if (!data) {
    return null;
  }

  const cards = [
    {
      icon: CloudRain,
      label: "Rain chance",
      value: `${data.rain.chance_pct}%`,
      sub: data.rain.will_it_rain ? "Carry an umbrella" : "No rain expected",
      accent: "text-rain",
      bar: data.rain.chance_pct,
    },
    {
      icon: Sunrise,
      label: "Sunrise / Sunset",
      value: data.sun.sunrise,
      sub: `Sets at ${data.sun.sunset}`,
      accent: "text-sun",
    },
    {
      icon: Gauge,
      label: "Pressure",
      value: `${data.pressure.hpa} hPa`,
      sub: data.pressure.hpa > 1013 ? "High pressure" : data.pressure.hpa < 1009 ? "Low pressure" : "Normal range",
      accent: "text-sky",
      bar: Math.min(100, Math.max(0, ((data.pressure.hpa - 980) / (1040 - 980)) * 100)),
    },
    {
      icon: Cloud,
      label: "Cloud cover",
      value: "75%",
      sub: "Mostly cloudy",
      accent: "text-sky",
      bar: 75,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-slide-up" style={{ animationDelay: "160ms" }}>
      {cards.map((c, i) => (
        <div
          key={c.label}
          className="group relative overflow-hidden rounded-xl p-4 bg-card border border-border hover:border-primary/30 transition-all hover:shadow-[var(--shadow-card)]"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[10px] font-semibold tracking-[0.12em] uppercase text-muted-foreground">
              <c.icon className={`h-3.5 w-3.5 ${c.accent}`} />
              {c.label}
            </div>
            <TrendingUp className="h-3 w-3 text-muted-foreground/60 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tracking-tight">{c.value}</span>
          </div>
          <div className="mt-1 text-[12px] text-muted-foreground">{c.sub}</div>
          {c.bar !== undefined && (
            <div className="mt-3 h-1 rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-primary-glow rounded-full transition-all duration-1000"
                style={{ width: `${c.bar}%`, animationDelay: `${i * 100}ms` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}