/**
 * useConversations Hook
 * Lists chat conversations for the current user or guest session.
 * Query key includes user/session context so cached data never leaks
 * between users or sessions.
 */

import { useQuery } from "@tanstack/react-query";
import { chatHistoryApi } from "@/lib/chat-history";
import type { ConversationSummary } from "@/lib/api-types";

export function useConversations(
  userId: number | null | undefined,
  sessionId: string | undefined,
  search: string = ""
) {
  const isGuest = userId == null;
  return useQuery<{ conversations: ConversationSummary[] }>({
    queryKey: [
      "chat",
      "conversations",
      userId ?? "guest",
      sessionId ?? "none",
      search,
    ],
    queryFn: () => chatHistoryApi.listConversations(isGuest ? sessionId : undefined, search),
    enabled: !isGuest || !!sessionId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    retry: 1,
  });
}
