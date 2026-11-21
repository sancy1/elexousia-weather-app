/**
 * Tests for apiClient request timeout behavior.
 * fetch is fully mocked — no live network calls.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { apiClient } from "./api-client";

function hungFetch() {
  return vi.fn(
    (_url: string, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(init.signal!.reason));
      })
  );
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("apiClient timeout", () => {
  it("aborts a hung request after the default 25s timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", hungFetch());

    const promise = apiClient.get("/api/test");
    const assertion = expect(promise).rejects.toMatchObject({ name: "TimeoutError" });
    await vi.advanceTimersByTimeAsync(25_000);
    await assertion;
  });

  it("resolves normally when the request completes before the timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const data = await apiClient.get<{ ok: boolean }>("/api/test");
    expect(data).toEqual({ ok: true });
  });

  it("honors a caller-provided abort signal", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", hungFetch());

    const controller = new AbortController();
    const promise = apiClient.get("/api/test", { signal: controller.signal });
    const assertion = expect(promise).rejects.toBeDefined();
    controller.abort(new DOMException("cancelled", "AbortError"));
    await assertion;
  });

  it("supports disabling the timeout per request", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", hungFetch());

    const promise = apiClient.get("/api/test", { timeoutMs: 0 });
    const settled = promise.then(
      () => "resolved" as const,
      () => "rejected" as const
    );

    await vi.advanceTimersByTimeAsync(60_000);
    // Still pending — the disabled timeout must not have fired.
    const winner = await Promise.race([settled, Promise.resolve("pending" as const)]);
    expect(winner).toBe("pending");
  });
});
