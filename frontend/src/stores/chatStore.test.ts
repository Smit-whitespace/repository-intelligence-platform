import { describe, expect, it, vi } from "vitest";
import { useChatStore } from "./chatStore";

describe("chatStore", () => {
  it("tracks user and streaming assistant messages", () => {
    vi.stubGlobal("crypto", {
      randomUUID: vi
        .fn()
        .mockReturnValueOnce("user-1")
        .mockReturnValueOnce("assistant-1"),
    });
    useChatStore.getState().clearConversation();

    useChatStore.getState().addUserMessage("Explain the repository");
    const assistantId = useChatStore.getState().startAssistantMessage();
    useChatStore.getState().appendAssistantChunk(assistantId, "Hello");
    useChatStore.getState().appendAssistantChunk(assistantId, " world");

    expect(useChatStore.getState().messages).toEqual([
      {
        id: "user-1",
        role: "user",
        content: "Explain the repository",
      },
      {
        id: "assistant-1",
        role: "assistant",
        content: "Hello world",
      },
    ]);
    expect(useChatStore.getState().isStreaming).toBe(true);

    useChatStore.getState().finishStreaming();

    expect(useChatStore.getState().isStreaming).toBe(false);
    vi.unstubAllGlobals();
  });
});
