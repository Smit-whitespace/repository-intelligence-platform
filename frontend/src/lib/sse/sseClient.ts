import { config } from "@/lib/config/env";
import { authorizationHeader, useAuthStore } from "@/stores/authStore";

type SseClientOptions = {
  onMessage: (message: string) => void;
  /** Named events (`event: <name>`), such as index progress. Never passed to onMessage. */
  onEvent?: (event: string, data: string) => void;
  /** Called once if the stream fails; not called after close(). */
  onError?: (error: Error) => void;
  /** Called once when the server ends the stream normally. */
  onDone?: () => void;
};

/**
 * Read a `text/event-stream` response with fetch.
 *
 * EventSource cannot send an Authorization header, and putting the API
 * token in the URL would write it into server logs (ADR-0020).
 */
export function createSseClient(path: string, options: SseClientOptions) {
  const controller = new AbortController();

  void (async () => {
    try {
      const response = await fetch(`${config.apiBaseUrl}${path}`, {
        headers: { Accept: "text/event-stream", ...authorizationHeader() },
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        if (response.status === 401) {
          useAuthStore.getState().markRejected();
        }

        throw new Error(`Stream failed with status ${response.status}`);
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += value.replace(/\r\n/g, "\n");
        let boundary = buffer.indexOf("\n\n");

        while (boundary !== -1) {
          const message = parseEvent(buffer.slice(0, boundary));
          buffer = buffer.slice(boundary + 2);
          boundary = buffer.indexOf("\n\n");

          if (message === null) {
            continue;
          }

          if (message.event === null) {
            options.onMessage(message.data);
          } else {
            options.onEvent?.(message.event, message.data);
          }
        }
      }

      options.onDone?.();
    } catch (error) {
      if (!controller.signal.aborted) {
        options.onError?.(error instanceof Error ? error : new Error(String(error)));
      }
    }
  })();

  return {
    close: () => controller.abort(),
  };
}

/**
 * Read one event block: its optional `event:` name and its `data:` lines
 * joined with "\n", as EventSource does.
 */
export function parseEvent(
  block: string,
): { event: string | null; data: string } | null {
  const lines = block.split("\n");
  const data = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, ""));

  if (!data.length) {
    return null;
  }

  const name = lines.find((line) => line.startsWith("event:"));
  const event = name ? name.slice(6).trim() : "";

  return { event: event || null, data: data.join("\n") };
}
