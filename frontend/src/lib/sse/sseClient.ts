import { config } from "@/lib/config/env";

type SseClientOptions = {
  onMessage: (message: string) => void;
  onError?: (event: Event) => void;
};

export function createSseClient(path: string, options: SseClientOptions) {
  const source = new EventSource(`${config.apiBaseUrl}${path}`);

  source.onmessage = (event) => {
    options.onMessage(event.data);
  };

  source.onerror = (event) => {
    options.onError?.(event);
  };

  return {
    close: () => source.close(),
  };
}
