import { Sparkles } from "lucide-react";
import type { ClothingAdviceResponse } from "@/lib/api-types";

interface Props {
  data?: ClothingAdviceResponse;
  unit: "C" | "F";
}

const cToDisplay = (c: number, u: "C" | "F") => (u === "C" ? c : Math.round((c * 9) / 5 + 32));

function getGradient(condition: string): string {
  const lower = condition.toLowerCase();
  if (lower.includes("rain") || lower.includes("drizzle")) {
    return "linear-gradient(135deg, oklch(0.42 0.10 240), oklch(0.55 0.14 220))";
  }
  if (lower.includes("snow")) {
    return "linear-gradient(135deg, oklch(0.50 0.06 230), oklch(0.70 0.05 220))";
  }
  if (lower.includes("sun") || lower.includes("clear")) {
    return "linear-gradient(135deg, oklch(0.62 0.16 60), oklch(0.72 0.14 35))";
  }
  return "linear-gradient(135deg, oklch(0.55 0.14 200), oklch(0.65 0.12 170))";
}

export function WhatToWear({ data, unit }: Props) {
  if (!data) {
    return null;
  }

  const gradient = getGradient(data.condition);
  const temp = unit === "C" ? data.temperature_c : data.temperature_f;

  return (
    <section
      className="relative overflow-hidden rounded-2xl border border-border animate-slide-up"
      style={{ animationDelay: "220ms" }}
    >
      <div className="absolute inset-0 opacity-90" style={{ background: gradient }} />
      <div className="absolute -top-16 -right-16 h-60 w-60 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute -bottom-20 -left-10 h-52 w-52 rounded-full bg-black/30 blur-3xl" />
      <svg className="absolute inset-0 h-full w-full opacity-[0.06]" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="white" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#dots)" />
      </svg>

      <div className="relative p-6 sm:p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-white/80 text-[11px] font-semibold tracking-[0.14em] uppercase">
              <Sparkles className="h-3 w-3" />
              What to wear today
            </div>
            <h3 className="mt-3 text-white text-2xl sm:text-3xl font-semibold tracking-tight">
              {data.summary}
            </h3>
            <p className="mt-1 text-white/75 text-sm">
              {data.tagline} · {cToDisplay(data.temperature_c, unit)}°{unit}
            </p>
          </div>
          <div className="text-5xl sm:text-6xl drop-shadow-lg animate-float">{data.emoji}</div>
        </div>

        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-3">
          {data.items.map((item) => (
            <div
              key={item.name}
              className="rounded-xl bg-white/10 backdrop-blur-md border border-white/15 p-3.5 hover:bg-white/15 transition-colors"
            >
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-white/15 flex items-center justify-center text-xl">
                  {item.icon}
                </div>
                <div className="min-w-0">
                  <div className="text-white text-[13px] font-semibold truncate">{item.name}</div>
                  <div className="text-white/65 text-[11px] truncate">{item.note}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 flex items-start gap-2.5 rounded-xl bg-black/25 backdrop-blur border border-white/10 px-4 py-3">
          <span className="text-base leading-none mt-0.5">💡</span>
          <p className="text-white/90 text-[13px] leading-relaxed">{data.tip}</p>
        </div>
      </div>
    </section>
  );
}