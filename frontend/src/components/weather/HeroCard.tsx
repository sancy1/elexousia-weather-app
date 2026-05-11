import { Droplets, Wind, Sun, Eye, MapPin, Sparkles } from "lucide-react";
import { conditionIcon, type Condition, conditionLabel } from "./data";

interface Props {
  city: string;
  country: string;
  time: string;
  temp: number;
  feels: number;
  condition: Condition;
  unit: "C" | "F";
  humidity?: number;
  windKph?: number;
  windDirection?: string;
  uvIndex?: number;
  visibilityKm?: number;
}

const convert = (c: number, u: "C" | "F") => (u === "C" ? c : Math.round((c * 9) / 5 + 32));

export function HeroCard({ city, country, time, temp, feels, condition, unit, humidity, windKph, windDirection, uvIndex, visibilityKm }: Props) {
  const Icon = conditionIcon[condition];
  
  const getHumidityLevel = (h: number) => {
    if (h >= 80) return "High";
    if (h >= 60) return "Moderate";
    return "Low";
  };
  
  const getUVLevel = (uv: number) => {
    if (uv >= 8) return "Very High";
    if (uv >= 6) return "High";
    if (uv >= 3) return "Moderate";
    return "Low";
  };
  
  const getVisibilityDesc = (v: number) => {
    if (v >= 10) return "Excellent";
    if (v >= 5) return "Good";
    return "Poor";
  };
  
  const stats = [
    { icon: Droplets, label: "Humidity", value: `${humidity ?? 0}%`, sub: getHumidityLevel(humidity ?? 0) },
    { icon: Wind, label: "Wind", value: `${windKph ?? 0} km/h`, sub: windDirection ?? "N/A" },
    { icon: Sun, label: "UV Index", value: `${uvIndex ?? 0}`, sub: getUVLevel(uvIndex ?? 0) },
    { icon: Eye, label: "Visibility", value: `${visibilityKm ?? 0} km`, sub: getVisibilityDesc(visibilityKm ?? 0) },
  ];
  
  return (
    <div className="relative overflow-hidden rounded-2xl p-6 sm:p-8 animate-slide-up" style={{ background: "var(--gradient-hero)" }}>
      <div className="absolute inset-0 opacity-80" style={{ background: "var(--gradient-glow)" }} />
      <div className="absolute -top-20 -right-20 h-80 w-80 rounded-full bg-primary-glow/20 blur-3xl" />
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

      <svg className="absolute inset-0 h-full w-full opacity-[0.04]" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <div className="relative flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-white/70 text-[11px] font-semibold tracking-[0.14em] uppercase">
            <Sparkles className="h-3 w-3" />
            Auto-detected
          </div>
          <div className="mt-3 flex items-center gap-2">
            <MapPin className="h-4 w-4 text-white/80" />
            <h2 className="text-white text-xl sm:text-2xl font-semibold tracking-tight">{city}</h2>
            <span className="text-white/60 text-sm">{country}</span>
          </div>
          <div className="mt-1 text-white/60 text-[12px]">{time}</div>
        </div>
        <div className="relative">
          <div className="absolute inset-0 bg-white/10 blur-2xl rounded-full" />
          <Icon className="relative h-20 w-20 sm:h-24 sm:w-24 text-white animate-float" strokeWidth={1.5} />
        </div>
      </div>

      <div className="relative mt-4 flex items-end gap-3">
        <span className="text-white text-[88px] sm:text-[110px] font-light leading-none tracking-tighter">
          {convert(temp, unit)}
        </span>
        <span className="text-white/70 text-3xl font-light mb-4">°{unit}</span>
      </div>
      <div className="relative text-white/85 text-sm">
        {conditionLabel[condition]} · Feels like {convert(feels, unit)}°{unit}
      </div>

      <div className="relative mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="rounded-xl bg-white/8 backdrop-blur-md border border-white/10 p-3 hover:bg-white/12 transition-colors">
            <div className="flex items-center gap-1.5 text-white/60 text-[10px] font-semibold tracking-[0.1em] uppercase">
              <s.icon className="h-3 w-3" />
              {s.label}
            </div>
            <div className="mt-1.5 text-white text-lg font-semibold">{s.value}</div>
            <div className="text-white/50 text-[10px]">{s.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
