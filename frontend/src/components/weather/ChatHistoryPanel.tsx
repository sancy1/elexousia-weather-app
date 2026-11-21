import { useMemo, useState } from "react";
import {
  ArrowLeft, Search, Plus, MessageSquare, MapPin, Loader2,
  AlertCircle, Inbox, RefreshCw, Trash2, User,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useConversations } from "@/hooks/useConversations";
import { chatHistoryApi } from "@/lib/chat-history";
import { toast } from "sonner";
import type { ConversationSummary } from "@/lib/api-types";

interface Props {
  onBack: () => void;
  onSelectConversation: (conv: ConversationSummary) => void;
  onNewChat: () => void;
  onConversationDeleted?: (conv: ConversationSummary) => void;
  sessionId?: string;
}

type GroupKey = "Today" | "Yesterday" | "Previous 7 days" | "Older";

function groupFor(dateStr: string | null): GroupKey {
  if (!dateStr) return "Older";
  const date = new Date(dateStr);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday.getTime() - 86400000);
  const startOfWeek = new Date(startOfToday.getTime() - 7 * 86400000);
  if (date >= startOfToday) return "Today";
  if (date >= startOfYesterday) return "Yesterday";
  if (date >= startOfWeek) return "Previous 7 days";
  return "Older";
}

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

const GROUP_ORDER: GroupKey[] = ["Today", "Yesterday", "Previous 7 days", "Older"];

export function ChatHistoryPanel({ onBack, onSelectConversation, onNewChat, onConversationDeleted, sessionId }: Props) {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [clearing, setClearing] = useState(false);
  const { data, isLoading, isError, refetch, isFetching } = useConversations(
    user?.id ?? null,
    sessionId,
    search
  );

  const conversations = data?.conversations ?? [];

  const handleDelete = async (conv: ConversationSummary) => {
    if (
      !window.confirm(
        `Delete "${conv.title}"?\n\nThis will permanently remove the conversation and all its messages.`
      )
    ) {
      return;
    }
    setDeletingId(conv.id);
    try {
      await chatHistoryApi.deleteConversation(conv.id, user ? undefined : sessionId);
      toast.success("Conversation deleted");
      onConversationDeleted?.(conv);
      refetch();
    } catch {
      toast.error("Couldn't delete the conversation. Try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    const scope = user ? "your account" : "this browser session";
    if (
      !window.confirm(
        `Delete all chat history?\n\nThis will permanently remove all saved conversations and messages for ${scope}.`
      )
    ) {
      return;
    }
    setClearing(true);
    try {
      const res = await chatHistoryApi.clearConversations(user ? undefined : sessionId);
      toast.success(`Cleared ${res.deleted} conversation${res.deleted === 1 ? "" : "s"}`);
      onConversationDeleted?.({ id: -1, session_id: sessionId ?? "", title: "", city_name: null, message_count: 0, created_at: null, last_active_at: null });
      refetch();
    } catch {
      toast.error("Couldn't clear history. Try again.");
    } finally {
      setClearing(false);
    }
  };

  const grouped = useMemo(() => {
    const map = new Map<GroupKey, ConversationSummary[]>();
    for (const key of GROUP_ORDER) map.set(key, []);
    for (const conv of conversations) {
      map.get(groupFor(conv.last_active_at ?? conv.created_at))!.push(conv);
    }
    return map;
  }, [conversations]);

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 h-[52px] border-b border-border shrink-0">
        <button
          onClick={onBack}
          className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          title="Back"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <span className="text-[13px] font-semibold tracking-tight flex-1">Chat History</span>
        <button
          onClick={() => refetch()}
          className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* New chat + search */}
      <div className="px-3 pt-3 space-y-2 shrink-0">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 h-9 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/40 text-primary text-[13px] font-medium transition-all"
        >
          <Plus className="h-4 w-4" />
          New chat
        </button>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations..."
            className="w-full h-9 pl-9 pr-3 rounded-lg bg-secondary/60 border border-border text-[13px] placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all"
          />
        </div>
        {!user && (
          <p className="text-[11px] text-muted-foreground flex items-start gap-1.5 px-1">
            <User className="h-3 w-3 mt-0.5 shrink-0" />
            Guest history is temporary and only visible in this browser session. Sign in to keep it across devices.
          </p>
        )}
      </div>

      {/* Clear all */}
      {conversations.length > 0 && (
        <div className="px-3 pt-2 shrink-0">
          <button
            onClick={handleClearAll}
            disabled={clearing}
            className="w-full flex items-center justify-center gap-2 h-8 rounded-lg text-[12px] text-destructive/80 hover:text-destructive hover:bg-destructive/10 border border-destructive/20 transition-all disabled:opacity-50"
          >
            {clearing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
            Clear all history
          </button>
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-2 mt-3 pb-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-5 w-5 animate-spin text-primary-glow" />
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center gap-2 py-10 px-4 text-center">
            <AlertCircle className="h-6 w-6 text-destructive" />
            <p className="text-[12px] text-muted-foreground">
              Couldn't load your chat history.
            </p>
            <button
              onClick={() => refetch()}
              className="text-[12px] text-primary-glow hover:underline"
            >
              Try again
            </button>
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 px-4 text-center">
            <Inbox className="h-6 w-6 text-muted-foreground" />
            <p className="text-[12px] text-muted-foreground">
              {search.trim()
                ? "No conversations match your search."
                : "No conversations yet. Start chatting to build your history."}
            </p>
          </div>
        ) : (
          GROUP_ORDER.map((group) => {
            const items = grouped.get(group)!;
            if (items.length === 0) return null;
            return (
              <div key={group} className="mb-3">
                <div className="px-2 mb-1.5">
                  <span className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
                    {group}
                  </span>
                </div>
                <div className="space-y-1">
                  {items.map((conv) => (
                    <div
                      key={conv.id}
                      className="w-full flex items-start gap-1 rounded-lg hover:bg-accent/40 transition-all group"
                    >
                      <button
                        onClick={() => onSelectConversation(conv)}
                        className="flex-1 flex items-start gap-3 px-3 py-2 text-left min-w-0"
                      >
                        <MessageSquare className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground group-hover:text-primary-glow transition-colors" />
                        <div className="flex-1 min-w-0">
                          <div className="text-[13px] font-medium truncate text-foreground">
                            {conv.title}
                          </div>
                          <div className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-2 truncate">
                            {conv.city_name && (
                              <span className="inline-flex items-center gap-1">
                                <MapPin className="h-2.5 w-2.5" />
                                {conv.city_name}
                              </span>
                            )}
                            <span>{relativeTime(conv.last_active_at ?? conv.created_at)}</span>
                            {conv.message_count > 0 && (
                              <span>· {conv.message_count} msg{conv.message_count === 1 ? "" : "s"}</span>
                            )}
                          </div>
                        </div>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(conv);
                        }}
                        disabled={deletingId === conv.id}
                        className="mt-1 mr-1.5 h-7 w-7 shrink-0 flex items-center justify-center rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all disabled:opacity-50"
                        title="Delete conversation"
                      >
                        {deletingId === conv.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
