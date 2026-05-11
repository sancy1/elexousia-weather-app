import { useState, useRef, useEffect } from "react";
import { Send, Mic, Paperclip } from "lucide-react";
import { quickChips } from "./data";

interface Props {
  onSend: (text: string) => void;
  isStreaming: boolean;
  currentCity?: string;
}

export function PromptBar({ onSend, isStreaming, currentCity }: Props) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const handleChipClick = (label: string) => {
    if (!currentCity) return;
    // Prepend city context to the chip message
    const message = `${label} for ${currentCity}`;
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
        {quickChips.map((chip) => (
          <button
            key={chip.label}
            onClick={() => handleChipClick(chip.label)}
            disabled={isStreaming || !currentCity}
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