import { afterEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/stores/authStore";
import { createSseClient, parseEvent } from "./sseClient";

afterEach(() => {
  vi.unstubAllGlobals();
  useAuthStore.setState({ token: null, rejected: false });
});

function streamOf(...parts: string[]) {
  const encoder = new TextEncoder();

  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const part of parts) {
        controller.enqueue(encoder.encode(part));
      }
      controller.close();
    },
  });
}

describe("parseEvent", () => {
  it("joins data lines with line breaks, as EventSource does", () => {
    expect(parseEvent("data: first\ndata: second")?.data).toBe("first\nsecond");
    expect(parseEvent("data:no space")?.data).toBe("no space");
    expect(parseEvent(": comment")).toBeNull();
  });

  it("separates named events from answer text", () => {
    expect(parseEvent('event: index\ndata: {"state":"updated"}')).toEqual({
      event: "index",
      data: '{"state":"updated"}',
    });
    expect(parseEvent("data: Hello")).toEqual({ event: null, data: "Hello" });
  });
});

describe("createSseClient", () => {
  it("sends the token and reads events split across chunks", async () => {
    useAuthStore.setState({ token: "secret" });

    const fetchMock = vi.fn(async () =>
      new Response(streamOf("data: Hel", "lo\n\ndata: line 1\ndata: line 2\n\n"), {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      }),
    );

    vi.stubGlobal("fetch", fetchMock);

    const messages: string[] = [];

    await new Promise<void>((resolve) => {
      createSseClient("/chat/stream?query=x", {
        onMessage: (message) => messages.push(message),
        onDone: resolve,
      });
    });

    expect(messages).toEqual(["Hello", "line 1\nline 2"]);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/chat/stream?query=x",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer secret" }),
      }),
    );
  });

  it("reports a refused stream and asks to sign in again", async () => {
    useAuthStore.setState({ token: "old" });

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 401 })),
    );

    const error = await new Promise<Error>((resolve) => {
      createSseClient("/chat/stream?query=x", {
        onMessage: () => undefined,
        onError: resolve,
      });
    });

    expect(error.message).toContain("401");
    expect(useAuthStore.getState().rejected).toBe(true);
  });

  it("sends named events to onEvent and unnamed ones to onMessage", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          streamOf(
            'event: index-progress\ndata: {"files":3}\n\n',
            "data: Hi\n\n",
          ),
          { status: 200 },
        ),
      ),
    );

    const messages: string[] = [];
    const events: Array<[string, string]> = [];

    await new Promise<void>((resolve) => {
      createSseClient("/chat/stream?query=x", {
        onMessage: (message) => messages.push(message),
        onEvent: (event, data) => events.push([event, data]),
        onDone: resolve,
      });
    });

    expect(messages).toEqual(["Hi"]);
    expect(events).toEqual([["index-progress", '{"files":3}']]);
  });
});
