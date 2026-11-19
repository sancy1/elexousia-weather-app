import { CloudSun } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "./data";

const markdownComponents = {
  p: ({ children }: any) => (
    <p className="text-[13.5px] leading-relaxed text-foreground/90 my-2 first:mt-0 last:mb-0">
      {children}
    </p>
  ),
  strong: ({ children }: any) => (
    <strong className="font-semibold text-foreground">{children}</strong>
  ),
  em: ({ children }: any) => <em className="italic">{children}</em>,
  ul: ({ children }: any) => (
    <ul className="list-disc pl-5 my-2 space-y-1 text-[13.5px] text-foreground/90">
      {children}
    </ul>
  ),
  ol: ({ children }: any) => (
    <ol className="list-decimal pl-5 my-2 space-y-1 text-[13.5px] text-foreground/90">
      {children}
    </ol>
  ),
  li: ({ children }: any) => <li className="leading-relaxed">{children}</li>,
  h1: ({ children }: any) => (
    <h1 className="text-base font-bold text-foreground mt-3 mb-1.5 first:mt-0">{children}</h1>
  ),
  h2: ({ children }: any) => (
    <h2 className="text-[15px] font-bold text-foreground mt-3 mb-1.5 first:mt-0">{children}</h2>
  ),
  h3: ({ children }: any) => (
    <h3 className="text-[14px] font-semibold text-foreground mt-2.5 mb-1 first:mt-0">{children}</h3>
  ),
  h4: ({ children }: any) => (
    <h4 className="text-[13.5px] font-semibold text-foreground mt-2 mb-1 first:mt-0">{children}</h4>
  ),
  table: ({ children }: any) => (
    <div className="my-3 overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-[12.5px] border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }: any) => <thead className="bg-muted/60">{children}</thead>,
  th: ({ children }: any) => (
    <th className="px-3 py-2 text-left font-semibold text-foreground border-b border-border whitespace-nowrap">
      {children}
    </th>
  ),
  td: ({ children }: any) => (
    <td className="px-3 py-2 text-foreground/85 border-b border-border/50 last:border-0 align-top">
      {children}
    </td>
  ),
  hr: () => <hr className="my-3 border-border" />,
  code: ({ children }: any) => (
    <code className="px-1.5 py-0.5 rounded bg-muted text-[12px] font-mono text-foreground/90">
      {children}
    </code>
  ),
  pre: ({ children }: any) => (
    <pre className="my-2 p-3 rounded-lg bg-muted overflow-x-auto text-[12px] font-mono text-foreground/90">
      {children}
    </pre>
  ),
  a: ({ children, href }: any) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-2">
      {children}
    </a>
  ),
  blockquote: ({ children }: any) => (
    <blockquote className="my-2 pl-3 border-l-2 border-primary/40 text-foreground/80 italic">
      {children}
    </blockquote>
  ),
};

interface Props {
  messages: ChatMessage[];
  isTyping: boolean;
  agentName?: string;
  dataLocation?: string;
  dataSource?: string;
}

export function ChatThread({ 
  messages, 
  isTyping, 
  agentName = "EL-Exousia Weather Agent",
  dataLocation = "",
  dataSource = "WeatherAPI.com"
}: Props) {
  return (
    <div className="space-y-4 animate-slide-up" style={{ animationDelay: "240ms" }}>
      <div className="relative flex items-center gap-3 my-4">
        <div className="flex-1 h-px bg-border" />
        <span className="text-[10px] font-semibold tracking-[0.18em] uppercase text-muted-foreground px-2">
          AI Assistant
        </span>
        <div className="flex-1 h-px bg-border" />
      </div>

      {messages.map((m) =>
        m.role === "user" ? (
          <div key={m.id} className="flex justify-end animate-slide-up">
            <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-gradient-to-br from-primary to-primary/80 text-primary-foreground px-4 py-2.5 text-[13.5px] leading-relaxed shadow-[0_4px_20px_-8px_var(--primary)]">
              {m.text}
              <div className="mt-1 text-[10px] text-white/60 text-right">{m.time}</div>
            </div>
          </div>
        ) : (
          <div key={m.id} className="animate-slide-up">
            <div className="rounded-2xl bg-card border border-border p-4 shadow-[var(--shadow-card)]">
              <div className="flex items-center gap-2 mb-3">
                <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center shadow-[0_0_15px_-4px_var(--primary-glow)]">
                  <CloudSun className="h-3.5 w-3.5 text-white" />
                </div>
                <div className="flex flex-col leading-tight">
                  <span className="text-[12px] font-semibold">{agentName}</span>
                  <span className="text-[10px] text-muted-foreground">{m.time}</span>
                </div>
                <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-medium">
                  Verified data
                </span>
              </div>
              <div className="text-foreground/90">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {m.text}
                </ReactMarkdown>
              </div>
              {dataLocation && (
                <div className="mt-3 pt-3 border-t border-border text-[10px] text-muted-foreground">
                  AI assisted weather analysis · {dataLocation}
                </div>
              )}
            </div>
          </div>
        )
      )}

      {isTyping && (
        <div className="rounded-2xl bg-card border border-border p-4 animate-fade-in">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
              <CloudSun className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-[12px] font-semibold">{agentName} is thinking…</span>
          </div>
          <div className="flex items-center gap-1.5 ml-9">
            <span className="h-2 w-2 rounded-full bg-primary-glow" style={{ animation: "typing-dot 1.2s ease-in-out infinite", animationDelay: "0ms" }} />
            <span className="h-2 w-2 rounded-full bg-primary-glow" style={{ animation: "typing-dot 1.2s ease-in-out infinite", animationDelay: "150ms" }} />
            <span className="h-2 w-2 rounded-full bg-primary-glow" style={{ animation: "typing-dot 1.2s ease-in-out infinite", animationDelay: "300ms" }} />
          </div>
        </div>
      )}
    </div>
  );
}