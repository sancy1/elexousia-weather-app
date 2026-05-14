import { useState, useRef, useEffect } from "react";
import { Send, Mic, Paperclip } from "lucide-react";
import { quickChips as fallbackChips } from "./data";

interface Props {
  onSend: (text: string) => void;
  isStreaming: boolean;
  currentCity?: string;
}

// List of cities to choose from for random comparisons
const COMPARISON_CITIES = [
  "Paris", "Tokyo", "New York", "Dubai", "Sydney", "London", "Barcelona", 
  "Amsterdam", "Singapore", "Toronto", "Bangkok", "Rome", "Berlin", "Madrid",
  "Istanbul", "Moscow", "Seoul", "Hong Kong", "Mumbai", "Cairo"
];

function getRandomCity(): string {
  return COMPARISON_CITIES[Math.floor(Math.random() * COMPARISON_CITIES.length)];
}

export function PromptBar({ onSend, isStreaming, currentCity }: Props) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const [chips, setChips] = useState<Array<{ id?: number; label: string; prompt_text?: string; icon: string; requires_city?: boolean }>>(fallbackChips as any);

  useEffect(() => {
    let mounted = true;
    const fetchChips = async () => {
      try {
        const res = await fetch('/api/chips');
        if (!res.ok) throw new Error('Failed to fetch chips');
        const data = await res.json();
        if (mounted && data && Array.isArray(data.chips)) setChips(data.chips);
      } catch (e) {
        // keep fallback chips
        console.warn('Could not fetch chips, using fallback', e);
      }
    };

    fetchChips();
    return () => { mounted = false; };
  }, []);

  const handleChipClick = (chip: { label: string; prompt_text?: string; requires_city?: boolean }) => {
    const label = chip.label;
    const prompt = chip.prompt_text || label;

    // If chip requires a city but we have no currentCity, don't do anything
    if (chip.requires_city && !currentCity) return;

    let message = '';

    // If this is a compare prompt (prompt_text starts with "Compare"), build two-city message
    if (/compare/i.test(prompt)) {
      const other = getRandomCity();
      // Some stored prompts are like "Compare the current weather in" -> append both cities
      message = `${prompt} ${currentCity} and ${other}`;
    }
    // Best day to travel -> ask for 7-day analysis
    else if (/best day to travel/i.test(prompt) || /travel/i.test(label) && /day/i.test(prompt)) {
      message = `${prompt} ${currentCity}. Consider the next 7 days and recommend the best day to travel.`;
    }
    // If prompt_text contains a placeholder or ends with preposition, just append the city
    else {
      message = `${prompt} ${currentCity}`.trim();
    }

    onSend(message);
  };

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = Math.min(ref.current.scrollHeight, 140) + "px";
    }
  }, [text]);

  const submit = () => {
    const t = text.trim();
    if (!t || isStreaming) return;
    onSend(t);
    setText("");
  };

  return (
    <div className="shrink-0 border-t border-border bg-background/80 backdrop-blur-xl px-4 sm:px-6 pt-3 pb-4">
      <div className="flex gap-2 overflow-x-auto scrollbar-thin pb-2 -mx-1 px-1">
        {chips.map((chip) => (
          <button
            key={chip.label}
            onClick={() => handleChipClick(chip)}
            disabled={isStreaming || (chip.requires_city && !currentCity)}
            className="shrink-0 flex items-center gap-1.5 h-8 px-3.5 rounded-full bg-secondary hover:bg-accent border border-border hover:border-primary/40 text-[12px] font-medium text-foreground/80 hover:text-foreground transition-all whitespace-nowrap disabled:opacity-50"
          >
            <span className="text-[13px] leading-none">{chip.icon}</span>
            {chip.label}
          </button>
        ))}
      </div>

      <div className="mt-2 flex items-end gap-2 rounded-2xl bg-secondary/60 border border-border focus-within:border-primary/50 focus-within:shadow-[0_0_0_3px_var(--primary)/15] transition-all p-2.5">
        <button className="h-9 w-9 shrink-0 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground transition-colors">
          <Paperclip className="h-4 w-4" />
        </button>
        <textarea
          ref={ref}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask about any city or get detailed forecast info…"
          spellCheck={true}
          className="flex-1 resize-none bg-transparent outline-none text-[14px] py-2 placeholder:text-muted-foreground max-h-[140px] scrollbar-thin"
        />
        <button className="h-9 w-9 shrink-0 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground transition-colors">
          <Mic className="h-4 w-4" />
        </button>
        <button
          onClick={submit}
          disabled={!text.trim() || isStreaming}
          className="h-10 w-10 shrink-0 flex items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-glow text-primary-foreground shadow-[0_4px_16px_-4px_var(--primary)] hover:shadow-[0_6px_24px_-4px_var(--primary-glow)] hover:scale-105 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isStreaming ? (
            <span className="h-3 w-3 bg-white rounded-sm" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
      <div className="mt-2 text-center text-[10px] text-muted-foreground">
        EL-Exousia can make mistakes. Verify forecasts before travel decisions.
      </div>
    </div>
  );
}