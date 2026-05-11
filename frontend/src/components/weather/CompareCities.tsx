import { useState } from "react";
import { ArrowRightLeft, Thermometer, Droplets, Wind, Sun, Flame, MapPin, Search, Sparkles, TrendingUp, TrendingDown } from "lucide-react";
import { useCompare } from "@/hooks/useCompare";
import type { CompareWeatherResponse } from "@/lib/api-types";

interface Props {
  unit: "C" | "F";
}

export function CompareCities({ unit }: Props) {
  const [cityA, setCityA] = useState("Lagos");
  const [cityB, setCityB] = useState("Kumasi");
  const [shouldCompare, setShouldCompare] = useState(false);
  
  const { data: result, isLoading, error } = useCompare(cityA, cityB, shouldCompare);

  const swap = () => {
    setCityA(cityB);
    setCityB(cityA);
  };

  const compare = () => {
    if (!cityA.trim() || !cityB.trim()) return;
    setShouldCompare(true);
  };

  const t = (c: number, f: number) => (unit === "C" ? `${Math.round(c)}°` : `${Math.round(f)}°`);
  const diff = result ? (unit === "C" ? result.comparison.temp_difference_c : result.comparison.temp_difference_f) : 0;

  return (
    <section className="rounded-3xl border border-border bg-card/60 backdrop-blur-xl shadow-[0_8px_40px_-16px_rgba(0,0,0,0.2)] overflow-hidden">
      {/* Header */}
      <div className="relative px-5 sm:px-6 pt-5 pb-4 border-b border-border/60">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-primary-glow/10 pointer-events-none" />
        <div className="relative flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center shadow-[0_4px_16px_-4px_var(--primary)]">
              <ArrowRightLeft className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h2 className="text-[15px] font-semibold tracking-tight">Compare cities</h2>
              <p className="text-[12px] text-muted-foreground">Side-by-side weather intelligence</p>
            </div>
          </div>
          <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
            <Sparkles className="h-3 w-3" /> Live
          </span>
        </div>
      </div>

      {/* Inputs */}
      <div className="px-5 sm:px-6 py-4 grid grid-cols-1 md:grid-cols-[1fr_auto_1fr_auto] gap-2 md:gap-3 items-center">
        <CityInput value={cityA} onChange={setCityA} placeholder="First city" />
        <button
          onClick={swap}
          aria-label="Swap"
          className="hidden md:flex h-10 w-10 items-center justify-center rounded-xl bg-secondary border border-border hover:border-primary/40 hover:bg-accent transition-all"
        >
          <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
        </button>
        <CityInput value={cityB} onChange={setCityB} placeholder="Second city" />
        <button
          onClick={compare}
          disabled={isLoading}
          className="h-10 px-5 rounded-xl bg-gradient-to-br from-primary to-primary-glow text-primary-foreground text-[13px] font-semibold shadow-[0_4px_16px_-4px_var(--primary)] hover:shadow-[0_6px_24px_-4px_var(--primary-glow)] hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
        >
          {isLoading ? "Comparing…" : "Compare"}
        </button>
      </div>

      {/* Result */}
      {error && (
        <div className="px-5 sm:px-6 pb-5 pt-1">
          <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-4 text-center">
            <p className="text-destructive text-sm">Failed to load comparison data. Please try again.</p>
          </div>
        </div>
      )}

      {result && (
        <div className="px-5 sm:px-6 pb-5 pt-1">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-3 md:gap-4 items-stretch">
            <CityCard data={result.city_1} unit={unit} accent="from-sky-500/20 to-cyan-400/10" isWarmer={result.comparison.warmer_city === result.city_1.city} />

            {/* VS pill / diff */}
            <div className="flex md:flex-col items-center justify-center gap-2 px-2">
              <div className="relative h-12 w-12 rounded-full bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center shadow-[0_6px_20px_-6px_var(--primary)] ring-4 ring-background">
                <span className="text-[11px] font-bold text-primary-foreground tracking-wider">VS</span>
              </div>
              <div className="flex flex-col items-center text-center">
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Δ Temp</span>
                <span className="text-[18px] font-bold bg-gradient-to-r from-primary to-primary-glow bg-clip-text text-transparent">
                  {Math.abs(diff).toFixed(1)}°{unit}
                </span>
              </div>
            </div>

            <CityCard data={result.city_2} unit={unit} accent="from-orange-500/20 to-rose-400/10" isWarmer={result.comparison.warmer_city === result.city_2.city} />
          </div>

          {/* Verdict */}
          <div className="mt-4 rounded-2xl border border-border bg-secondary/50 p-4 flex items-start gap-3">
            <div className="h-9 w-9 shrink-0 rounded-lg bg-gradient-to-br from-amber-400/30 to-orange-500/20 flex items-center justify-center">
              <Flame className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-[13px] leading-relaxed">
              <span className="font-semibold text-foreground">{result.comparison.warmer_city}</span>
              <span className="text-muted-foreground"> is warmer than </span>
              <span className="font-semibold text-foreground">{result.comparison.cooler_city}</span>
              <span className="text-muted-foreground"> by </span>
              <span className="font-semibold text-primary">{Math.abs(diff).toFixed(1)}°{unit}</span>
              <span className="text-muted-foreground">.</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function CityInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <div className="relative group">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full h-10 pl-9 pr-3 rounded-xl bg-secondary/70 border border-border focus:border-primary/50 focus:bg-background outline-none text-[13px] font-medium placeholder:text-muted-foreground/70 transition-all"
      />
    </div>
  );
}

function CityCard({ data, unit, accent, isWarmer }: { data: any; unit: "C" | "F"; accent: string; isWarmer: boolean }) {
  const temp = unit === "C" ? data.temperature_c : data.temperature_f;
  const feels = unit === "C" ? data.feels_like_c : (data.feels_like_c * 9) / 5 + 32;

  return (
    <div className={`relative rounded-2xl border border-border bg-gradient-to-br ${accent} p-4 overflow-hidden group hover:border-primary/30 transition-all`}>
      <div className="absolute -top-10 -right-10 h-32 w-32 rounded-full bg-white/10 blur-2xl pointer-events-none" />

      <div className="relative flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-medium">
            <MapPin className="h-3 w-3" />
            <span className="truncate">{data.country}</span>
          </div>
          <h3 className="mt-0.5 text-[18px] font-bold tracking-tight truncate">{data.city}</h3>
        </div>
        {isWarmer ? (
          <span className="shrink-0 flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-600 border border-amber-500/30">
            <TrendingUp className="h-2.5 w-2.5" /> Warmer
          </span>
        ) : (
          <span className="shrink-0 flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-500/15 text-sky-600 border border-sky-500/30">
            <TrendingDown className="h-2.5 w-2.5" /> Cooler
          </span>
        )}
      </div>

      <div className="relative mt-3 flex items-end gap-2">
        <span className="text-[44px] font-bold leading-none tracking-tighter">{Math.round(temp)}°</span>
        <span className="mb-1.5 text-[12px] text-muted-foreground">Feels {Math.round(feels)}°</span>
      </div>
      <p className="relative mt-1 text-[12px] text-foreground/70 line-clamp-1">{data.condition}</p>

      <div className="relative mt-3 grid grid-cols-3 gap-2">
        <Stat icon={Droplets} value={`${data.humidity_pct}%`} label="Humidity" />
        <Stat icon={Wind} value={`${Math.round(data.wind_kph)} kph`} label="Wind" />
        <Stat icon={Sun} value={`${data.uv_index}`} label="UV" />
      </div>
    </div>
  );
}

function Stat({ icon: Icon, value, label }: { icon: typeof Thermometer; value: string; label: string }) {
  return (
    <div className="rounded-lg bg-background/50 border border-border/60 p-2 backdrop-blur-sm">
      <Icon className="h-3 w-3 text-muted-foreground" />
      <div className="mt-1 text-[12px] font-semibold leading-none">{value}</div>
      <div className="mt-1 text-[9px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}