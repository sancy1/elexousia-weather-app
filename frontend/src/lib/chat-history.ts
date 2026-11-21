/**
 * Chat History API Client
 * Conversation list + message loading for the sidebar history panel.
 */

import { apiClient } from "./api-client";
import type { QueryClient } from "@tanstack/react-query";
import type { ConversationSummary, ConversationExchange } from "./api-types";

/**
 * Optimistically prepend a temporary conversation entry for `sessionId`
 * to every cached ["chat", "conversations"] query. Skips if the session is
 * already tracked (prevents duplicates). The temp entry uses a negative id
 * and is replaced by the real server row on the next invalidation/refetch.
 */
export function optimisticAddConversation(
  queryClient: QueryClient,
  sessionId: string,
  title: string,
  cityName: string | null
): void {
  const now = new Date().toISOString();
  queryClient.setQueriesData<{ conversations: ConversationSummary[] }>(
    { queryKey: ["chat", "conversations"] },
    (old) => {
      if (!old) return old;
      if (old.conversations.some((c) => c.session_id === sessionId)) {
        return old;
      }
      const temp: ConversationSummary = {
        id: -Date.now(),
        session_id: sessionId,
        title: title.trim().slice(0, 80) || "Weather chat",
        city_name: cityName,
        message_count: 0,
        created_at: now,
        last_active_at: now,
      };
      return { conversations: [temp, ...old.conversations] };
    }
  );
}

export const chatHistoryApi = {
  /**
   * List conversations for the current user (auth) or guest session.
   * sessionId is only sent for guests; the backend ignores it for auth users.
   */
  async listConversations(
    sessionId?: string,
    search?: string
  ): Promise<{ conversations: ConversationSummary[] }> {
    const params = new URLSearchParams();
    if (sessionId) params.set("session_id", sessionId);
    if (search && search.trim()) params.set("q", search.trim());
    const qs = params.toString();
    return apiClient.get<{ conversations: ConversationSummary[] }>(
      `/api/chat/conversations${qs ? `?${qs}` : ""}`
    );
  },

  /**
   * Load exchanges for one conversation (ownership verified server-side).
   */
  async getMessages(
    conversationId: number,
    sessionId?: string
  ): Promise<{ messages: ConversationExchange[] }> {
    const params = new URLSearchParams();
    if (sessionId) params.set("session_id", sessionId);
    const qs = params.toString();
    return apiClient.get<{ messages: ConversationExchange[] }>(
      `/api/chat/conversations/${conversationId}/messages${qs ? `?${qs}` : ""}`
    );
  },

  /**
   * Permanently delete one conversation (ownership verified server-side).
   */
  async deleteConversation(
    conversationId: number,
    sessionId?: string
  ): Promise<{ deleted: boolean }> {
    const params = new URLSearchParams();
    if (sessionId) params.set("session_id", sessionId);
    const qs = params.toString();
    return apiClient.delete<{ deleted: boolean }>(
      `/api/chat/conversations/${conversationId}${qs ? `?${qs}` : ""}`
    );
  },

  /**
   * Permanently delete ALL conversations visible to the caller
   * (own user history, or this guest session's history only).
   */
  async clearConversations(sessionId?: string): Promise<{ deleted: number }> {
    const params = new URLSearchParams();
    if (sessionId) params.set("session_id", sessionId);
    const qs = params.toString();
    return apiClient.delete<{ deleted: number }>(
      `/api/chat/conversations${qs ? `?${qs}` : ""}`
    );
  },
};
