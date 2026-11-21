/**
 * Tests for optimisticAddConversation — immediate chat-history updates.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { optimisticAddConversation } from "./chat-history";
import type { ConversationSummary } from "./api-types";

const KEY = ["chat", "conversations"];

function conv(partial: Partial<ConversationSummary>): ConversationSummary {
  return {
    id: 1,
    session_id: "sess-a",
    title: "Existing chat",
    city_name: null,
    message_count: 2,
    created_at: "2026-11-21T10:00:00Z",
    last_active_at: "2026-11-21T10:00:00Z",
    ...partial,
  };
}

function seed(qc: QueryClient, conversations: ConversationSummary[], search = "") {
  qc.setQueryData(
    [...KEY, 1, "guest", "sess-x", search],
    { conversations }
  );
}

function read(qc: QueryClient, search = "") {
  return qc.getQueryData<{ conversations: ConversationSummary[] }>([
    ...KEY, 1, "guest", "sess-x", search,
  ])?.conversations;
}

let qc: QueryClient;
beforeEach(() => {
  qc = new QueryClient();
});

describe("optimisticAddConversation", () => {
  it("adds a temporary entry immediately for a new session", () => {
    seed(qc, [conv({ id: 5 })]);
    optimisticAddConversation(qc, "sess-new", "What is the weather in Lagos?", "Lagos");

    const list = read(qc)!;
    expect(list).toHaveLength(2);
    expect(list[0].session_id).toBe("sess-new");
    expect(list[0].title).toBe("What is the weather in Lagos?");
    expect(list[0].city_name).toBe("Lagos");
    expect(list[0].id).toBeLessThan(0); // temp id
    expect(list[0].created_at).toBeTruthy();
  });

  it("does not create a duplicate for an already-tracked session", () => {
    seed(qc, [conv({ id: 5, session_id: "sess-a" })]);
    optimisticAddConversation(qc, "sess-a", "follow-up message", null);

    const list = read(qc)!;
    expect(list).toHaveLength(1);
    expect(list[0].id).toBe(5);
  });

  it("updates every cached query variant (e.g. different search terms)", () => {
    seed(qc, [], "");
    seed(qc, [], "lagos");
    optimisticAddConversation(qc, "sess-new", "hi", null);

    expect(read(qc, "")!.some((c) => c.session_id === "sess-new")).toBe(true);
    expect(read(qc, "lagos")!.some((c) => c.session_id === "sess-new")).toBe(true);
  });

  it("truncates long titles and falls back for empty input", () => {
    seed(qc, []);
    optimisticAddConversation(qc, "s1", "x".repeat(200), null);
    optimisticAddConversation(qc, "s2", "   ", null);

    const list = read(qc)!;
    expect(list.find((c) => c.session_id === "s1")!.title.length).toBeLessThanOrEqual(80);
    expect(list.find((c) => c.session_id === "s2")!.title).toBe("Weather chat");
  });

  it("is a no-op when no conversations query is cached", () => {
    // No seed — setQueriesData must not create phantom entries
    optimisticAddConversation(qc, "sess-new", "hi", null);
    expect(qc.getQueryCache().getAll()).toHaveLength(0);
  });
});
