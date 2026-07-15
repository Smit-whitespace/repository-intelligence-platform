import { create } from "zustand";

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

type ChatState = {
  messages: ChatMessage[];
  isStreaming: boolean;
  addUserMessage: (content: string) => void;
  startAssistantMessage: () => string;
  appendAssistantChunk: (id: string, content: string) => void;
  finishStreaming: () => void;
  clearConversation: () => void;
};

function messageId() {
  return crypto.randomUUID();
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  addUserMessage: (content) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: messageId(),
          role: "user",
          content,
        },
      ],
    })),
  startAssistantMessage: () => {
    const id = messageId();

    set((state) => ({
      isStreaming: true,
      messages: [
        ...state.messages,
        {
          id,
          role: "assistant",
          content: "",
        },
      ],
    }));

    return id;
  },
  appendAssistantChunk: (id, content) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === id
          ? {
              ...message,
              content: `${message.content}${content}`,
            }
          : message,
      ),
    })),
  finishStreaming: () =>
    set({
      isStreaming: false,
    }),
  clearConversation: () =>
    set({
      messages: [],
      isStreaming: false,
    }),
}));
