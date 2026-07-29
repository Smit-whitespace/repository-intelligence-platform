import { Copy, Send, Square, Trash2 } from "lucide-react";
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
  const inputRef = useRef<HTMLTextAreaElement>(null);

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

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <section className="animate-fade-in flex h-full flex-col">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[#F8FAFC]">Chat</h1>
          <p className="mt-1 text-sm text-[#7A8599]">
            Repository-aware conversation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-[var(--radius-sm)] bg-[#1A2335] px-3 py-1.5 text-xs text-[#AAB4C5]">
            {activeModel.data?.active_model ?? "loading"}
          </span>
          {messages.length > 0 ? (
            <Button
              variant="ghost"
              onClick={() => {
                clearConversation();
                setError(null);
              }}
              disabled={isStreaming}
              className="h-8 px-2"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          ) : null}
        </div>
      </div>

      {activeModel.isError ? <ApiErrorState error={activeModel.error} /> : null}

      <div
        ref={listRef}
        className="flex-1 overflow-y-auto"
      >
        {messages.length ? (
          <div className="space-y-6">
            {messages.map((message) => (
              <MessageBlock key={message.id} message={message} />
            ))}
            {isStreaming ? (
              <div className="flex items-center gap-2 pl-9">
                <span className="h-1.5 w-1.5 animate-pulse-blue rounded-full bg-[#4F8CFF]" />
                <span className="text-xs text-[#7A8599]">Generating response</span>
              </div>
            ) : null}
          </div>
        ) : (
          <EmptyState
            title="Ask a repository question"
            description="Type a question about your open repository. RIP will retrieve relevant context and generate an answer."
            className="min-h-48"
          />
        )}
      </div>

      {error ? (
        <div className="mb-4 rounded-[var(--radius-sm)] border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.06)] px-4 py-3 text-sm text-[#EF4444]">
          {error}
        </div>
      ) : null}

      <form
        className="mt-4"
        onSubmit={(event) => {
          event.preventDefault();
          sendMessage();
        }}
      >
        <label className="sr-only" htmlFor="chatQuery">
          Chat query
        </label>
        <div className="relative rounded-[var(--radius)] border border-[rgba(255,255,255,0.1)] bg-[#111827] transition-colors focus-within:border-[#4F8CFF]/50">
          <textarea
            ref={inputRef}
            id="chatQuery"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your repository..."
            rows={3}
            className="min-h-[52px] w-full resize-none bg-transparent px-4 py-3.5 pr-12 text-sm text-[#F8FAFC] placeholder-[#7A8599] outline-none"
          />
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            {isStreaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-gradient-to-r from-[#4F8CFF] to-[#8B5CF6] text-white transition hover:opacity-90"
              >
                <Square className="h-3.5 w-3.5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!query.trim()}
                className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-gradient-to-r from-[#4F8CFF] to-[#8B5CF6] text-white transition hover:opacity-90 disabled:opacity-30"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
        <p className="mt-2 text-xs text-[#7A8599]">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </section>
  );
}

function MessageBlock({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <article className="animate-slide-in group">
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] text-[11px] font-semibold",
            isUser
              ? "bg-[#1A2335] text-[#AAB4C5]"
              : "bg-gradient-to-br from-[#4F8CFF] to-[#8B5CF6] text-white",
          )}
        >
          {isUser ? "U" : "R"}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className="text-xs font-medium text-[#F8FAFC]">
              {isUser ? "You" : "RIP"}
            </span>
            <button
              type="button"
              onClick={() => {
                void navigator.clipboard.writeText(message.content);
                toast.success("Message copied");
              }}
              className="opacity-0 transition-opacity group-hover:opacity-100"
            >
              <Copy className="h-3 w-3 text-[#7A8599] hover:text-[#F8FAFC]" />
            </button>
          </div>
          <div className="text-sm leading-relaxed text-[#AAB4C5]">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : message.content ? (
              <MarkdownMessage content={message.content} />
            ) : (
              <p className="text-[#7A8599]">Waiting for response...</p>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
