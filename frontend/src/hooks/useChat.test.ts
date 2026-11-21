/**
 * Tests for useChat SSE streaming — mocked stream, no network.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "./useChat";
import { weatherApi } from "@/lib/weather";

vi.mock("@/lib/weather", () => ({
  weatherApi: { chatStream: vi.fn() },
}));

const mockedChatStream = vi.mocked(weatherApi.chatStream);

/** Build a ReadableStream that enqueues the given string chunks. */
function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
}

function sse(event: object): string {
  return `data: ${JSON.stringify(event)}\n\n`;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("useChat streaming", () => {
  it("accumulates token events into currentResponse", async () => {
    mockedChatStream.mockResolvedValue(
      streamFromChunks([
        sse({ type: "token", content: "Hello " }),
        sse({ type: "token", content: "world" }),
        sse({ type: "done" }),
      ]) as never
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("hi");
    });

    expect(result.current.currentResponse).toBe("Hello world");
    expect(result.current.isStreaming).toBe(false);
  });

  it("reassembles SSE events split across chunk boundaries", async () => {
    const full =
      sse({ type: "token", content: "part-A" }) + sse({ type: "token", content: "part-B" }) + sse({ type: "done" });
    // Split mid-event — the parser must buffer the incomplete tail
    const mid = Math.floor(full.length / 2);
    mockedChatStream.mockResolvedValue(
      streamFromChunks([full.slice(0, mid), full.slice(mid)]) as never
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("hi");
    });

    expect(result.current.currentResponse).toBe("part-Apart-B");
  });

  it("emits resolved_city from tool-call events", async () => {
    mockedChatStream.mockResolvedValue(
      streamFromChunks([
        sse({ type: "resolved_city", city: "Lagos" }),
        sse({ type: "token", content: "ok" }),
        sse({ type: "done" }),
      ]) as never
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("what to wear in Lagos?");
    });

    expect(result.current.resolvedCity).toBe("Lagos");
  });

  it("shows a friendly error on stream failure event", async () => {
    mockedChatStream.mockResolvedValue(
      streamFromChunks([sse({ type: "error", detail: "internal stack trace sk-xyz" })]) as never
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("hi");
    });

    expect(result.current.currentResponse).not.toContain("sk-xyz");
    expect(result.current.currentResponse.length).toBeGreaterThan(0);
    expect(result.current.isStreaming).toBe(false);
  });

  it("passes an AbortSignal to chatStream", async () => {
    mockedChatStream.mockResolvedValue(streamFromChunks([sse({ type: "done" })]) as never);

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("hi");
    });

    const callArgs = mockedChatStream.mock.calls[0];
    expect(callArgs[4]).toBeInstanceOf(AbortSignal);
  });

  it("stopChat aborts the in-flight request", async () => {
    // Stream that never closes until aborted
    mockedChatStream.mockImplementation(
      (_m, _s, _c, _u, signal) =>
        new Promise((resolve, reject) => {
          signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }) as never
    );

    const { result } = renderHook(() => useChat());
    let pending: Promise<string>;
    await act(async () => {
      pending = result.current.sendMessage("hi");
    });
    await waitFor(() => expect(result.current.isStreaming).toBe(true));

    act(() => result.current.stopChat());
    await act(async () => {
      await pending!;
    });

    expect(result.current.isStreaming).toBe(false);
  });
});
