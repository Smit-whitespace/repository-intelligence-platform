import { Copy, RefreshCw, Send, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/Button";
import { useActiveModel } from "@/lib/api/queries";
import { createSseClient } from "@/lib/sse/sseClient";
import { cn } from "@/lib/utils/cn";
import { useProjectStore } from "@/stores/projectStore";
import { useChatStore, type ChatMessage } from "@/stores/chatStore";
import { MarkdownMessage } from "./MarkdownMessage";

type StreamClient = ReturnType<typeof createSseClient>;

export function ChatPage() {
  const activeProject = useProjectStore((state) => state.activeProject);
  const activeModel = useActiveModel();
  const messages = useChatStore((state) => state.messages);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const addUserMessage = useChatStore((state) => state.addUserMessage);
  const startAssistantMessage = useChatStore((state) => state.startAssistantMessage);
  const appendAssistantChunk = useChatStore((state) => state.appendAssistantChunk);
  const finishStreaming = useChatStore((state) => state.finishStreaming);
  const clearConversation = useChatStore((state) => state.clearConversation);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const streamRef = useRef<StreamClient | null>(null);
  const hadContentRef = useRef(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  useEffect(
    () => () => {
      streamRef.current?.close();
    },
    [],
  );

  function stopStreaming() {
    streamRef.current?.close();
    streamRef.current = null;
    finishStreaming();
  }

  function sendMessage() {
    const trimmedQuery = query.trim();

    if (!trimmedQuery || isStreaming) {
      return;
    }

    setError(null);
    setQuery("");
    hadContentRef.current = false;
    addUserMessage(trimmedQuery);
    const assistantId = startAssistantMessage();

    streamRef.current = createSseClient(
      `/chat/stream?${new URLSearchParams({
        query: trimmedQuery,
      }).toString()}`,
      {
        onMessage: (message) => {
          hadContentRef.current = true;
          appendAssistantChunk(assistantId, message);
        },
        onError: () => {
          streamRef.current?.close();
          streamRef.current = null;
          finishStreaming();

          if (!hadContentRef.current) {
            setError("Chat stream failed before a response was received.");
          }
        },
      },
    );
  }

  return (
    <section className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <h2 className="text-xl font-semibold">Chat</h2>
          <p className="text-sm text-muted-foreground">
            Repository-aware conversation using the active backend model.
          </p>
        </div>
        <div className="rounded-md border border-border bg-surface px-3 py-2 text-sm">
          <span className="text-muted-foreground">Model </span>
          <span className="font-medium">
            {activeModel.data?.active_model ?? "loading"}
          </span>
        </div>
      </div>
      {activeModel.isError ? <ApiErrorState error={activeModel.error} /> : null}
      {!activeProject ? (
        <EmptyState
          title="No project open"
          description="Open a project to provide repository context for chat."
        />
      ) : null}
      <div
        ref={listRef}
        className="min-h-[24rem] flex-1 overflow-y-auto rounded-md border border-border bg-surface p-4"
      >
        {messages.length ? (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isStreaming ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
                Streaming response
              </div>
            ) : null}
          </div>
        ) : (
          <EmptyState
            title="Ask a repository question"
            description="Questions are sent to the backend chat stream and answered with repository context."
          />
        )}
      </div>
      {error ? (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600">
          {error}
        </div>
      ) : null}
      <form
        className="rounded-md border border-border bg-surface p-3"
        onSubmit={(event) => {
          event.preventDefault();
          sendMessage();
        }}
      >
        <label className="sr-only" htmlFor="chatQuery">
          Chat query
        </label>
        <textarea
          id="chatQuery"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask about the open repository..."
          className="min-h-24 w-full resize-none rounded-md border border-border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-primary"
        />
        <div className="mt-3 flex flex-wrap justify-between gap-2">
          <Button
            className="bg-muted text-foreground"
            onClick={() => {
              clearConversation();
              setError(null);
            }}
            disabled={isStreaming || messages.length === 0}
          >
            <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" />
            Clear
          </Button>
          <div className="flex gap-2">
            {isStreaming ? (
              <Button className="bg-muted text-foreground" onClick={stopStreaming}>
                <X className="mr-2 h-4 w-4" aria-hidden="true" />
                Stop
              </Button>
            ) : null}
            <Button type="submit" disabled={!query.trim() || isStreaming}>
              <Send className="mr-2 h-4 w-4" aria-hidden="true" />
              Send
            </Button>
          </div>
        </div>
      </form>
    </section>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <article
      className={cn(
        "rounded-md border border-border p-3",
        isUser ? "ml-auto max-w-[80%] bg-primary text-primary-foreground" : "bg-background",
      )}
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase">
          {isUser ? "You" : "RIP"}
        </span>
        <Button
          className={cn(
            "h-7 bg-muted px-2 text-foreground",
            isUser && "bg-primary-foreground text-primary",
          )}
          onClick={() => {
            void navigator.clipboard.writeText(message.content);
            toast.success("Message copied");
          }}
        >
          <Copy className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
          Copy
        </Button>
      </div>
      {isUser ? (
        <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
      ) : message.content ? (
        <MarkdownMessage content={message.content} />
      ) : (
        <p className="text-sm text-muted-foreground">Waiting for response...</p>
      )}
    </article>
  );
}
