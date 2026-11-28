import { act, fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChatStore } from "@/stores/chatStore";
import { useProjectStore } from "@/stores/projectStore";
import { ChatPage } from "./ChatPage";

type Options = {
  onMessage: (message: string) => void;
  onEvent?: (event: string, data: string) => void;
  onError?: (error: Error) => void;
  onDone?: () => void;
};

const mocks = vi.hoisted(() => ({ options: null as Options | null }));

vi.mock("@/lib/sse/sseClient", () => ({
  createSseClient: (_path: string, options: Options) => {
    mocks.options = options;
    return { close: vi.fn() };
  },
}));

vi.mock("@/lib/api/queries", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api/queries")>()),
  useActiveModel: () => ({ data: { active_model: "m" }, isError: false }),
}));

const NOTE = "Updated 2 of 5 files; the rest will update on the next question.";

const partial = JSON.stringify({
  state: "partial",
  changed_files: 5,
  added_files: 0,
  removed_files: 0,
  updated_files: 2,
  pending_files: 3,
  seconds: 20,
  note: NOTE,
});

function renderPage(client = new QueryClient()) {
  render(
    <QueryClientProvider client={client}>
      <ChatPage />
    </QueryClientProvider>,
  );

  return client;
}

const updated = JSON.stringify({
  state: "updated",
  changed_files: 1,
  added_files: 0,
  removed_files: 0,
  updated_files: 1,
  pending_files: 0,
  seconds: 1,
  note: null,
});

async function ask() {
  const box = screen.getByLabelText("Chat query");
  await act(async () => {
    fireEvent.change(box, { target: { value: "hello" } });
    fireEvent.submit(box.closest("form")!);
  });
}

beforeEach(() => {
  Element.prototype.scrollTo = vi.fn();
  mocks.options = null;
  useChatStore.setState({ messages: [], isStreaming: false });
  useProjectStore.setState({
    activeProject: { name: "p", root_directory: "A:/repo" },
  } as never);
});

describe("ChatPage index updates", () => {
  it("shows the update progress, then the note for a partial update", async () => {
    renderPage();
    await ask();

    act(() => mocks.options!.onEvent!("index-progress", '{"files":3}'));
    expect(screen.getByText("Updating index (3 files)…")).toBeInTheDocument();

    act(() => mocks.options!.onEvent!("index", partial));
    expect(screen.queryByText(/Updating index/)).not.toBeInTheDocument();
    expect(screen.getByText(NOTE)).toBeInTheDocument();

    act(() => mocks.options!.onMessage("The answer"));
    expect(screen.getByText("The answer")).toBeInTheDocument();
    expect(screen.getByText(NOTE)).toBeInTheDocument();
  });

  it("says 1 file, not 1 files", async () => {
    renderPage();
    await ask();

    act(() => mocks.options!.onEvent!("index-progress", '{"files":1}'));

    expect(screen.getByText("Updating index (1 file)…")).toBeInTheDocument();
  });

  it("hides the progress line when the answer starts", async () => {
    renderPage();
    await ask();

    act(() => mocks.options!.onEvent!("index-progress", '{"files":1}'));
    act(() => mocks.options!.onMessage("Answer"));

    expect(screen.queryByText(/Updating index/)).not.toBeInTheDocument();
  });

  it("shows nothing for an update that finished", async () => {
    renderPage();
    await ask();

    act(() => mocks.options!.onEvent!("index-progress", '{"files":1}'));
    act(() => mocks.options!.onEvent!("index", updated));

    expect(screen.queryByText(/Updating index/)).not.toBeInTheDocument();
    expect(screen.queryByText(/files/)).not.toBeInTheDocument();
  });

  it("shows the detail of an error event", async () => {
    renderPage();
    await ask();

    act(() =>
      mocks.options!.onEvent!(
        "error",
        JSON.stringify({ status: 502, detail: "Ollama is not reachable." }),
      ),
    );

    expect(screen.getByText("Ollama is not reachable.")).toBeInTheDocument();
    expect(useChatStore.getState().isStreaming).toBe(false);
  });

  it("does not count named events as answer content", async () => {
    renderPage();
    await ask();

    act(() => mocks.options!.onEvent!("index-progress", '{"files":1}'));
    act(() => mocks.options!.onError!(new Error("boom")));

    expect(
      screen.getByText("Chat stream failed before a response was received."),
    ).toBeInTheDocument();
  });

  it("refreshes the index state after a stream that updated the index", async () => {
    const client = renderPage();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    await ask();

    act(() => mocks.options!.onEvent!("index", updated));
    act(() => mocks.options!.onMessage("Answer"));
    expect(invalidate).not.toHaveBeenCalled();

    act(() => mocks.options!.onDone!());

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["workspace", "index-status", "A:/repo"],
    });
  });

  it("leaves the index state alone when the stream sent no index event", async () => {
    const client = renderPage();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    await ask();

    act(() => mocks.options!.onMessage("Answer"));
    act(() => mocks.options!.onDone!());

    expect(invalidate).not.toHaveBeenCalled();
  });
});
