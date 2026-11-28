import { act, renderHook } from "@testing-library/react";
import { focusManager, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { FreshnessResult } from "@/types/api";
import {
  INDEX_STATUS_POLL_MS,
  indexStatusRefetchInterval,
  useIndexStatus,
} from "./queries";

const mocks = vi.hoisted(() => ({ indexStatus: vi.fn() }));

vi.mock("./endpoints", () => ({
  api: { indexStatus: mocks.indexStatus },
}));

function status(state: FreshnessResult["state"]): FreshnessResult {
  return {
    state,
    changed_files: 0,
    added_files: 0,
    removed_files: 0,
    updated_files: 0,
    pending_files: 0,
    seconds: 0,
    note: null,
  };
}

let client: QueryClient;

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  vi.useFakeTimers();
  // jsdom is not "visible", and polling pauses in a background tab.
  focusManager.setFocused(true);
  // The app's default: cached data counts as fresh for 30 s.
  client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 30_000 } },
  });
  mocks.indexStatus.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
  focusManager.setFocused(undefined);
});

describe("useIndexStatus", () => {
  it("polls only while the index is updating", () => {
    expect(indexStatusRefetchInterval(status("updating"))).toBe(INDEX_STATUS_POLL_MS);
    expect(indexStatusRefetchInterval(status("up_to_date"))).toBe(false);
    expect(indexStatusRefetchInterval(status("stale"))).toBe(false);
    expect(indexStatusRefetchInterval(undefined)).toBe(false);
  });

  it("re-reads the state every few seconds until the update ends", async () => {
    mocks.indexStatus
      .mockResolvedValueOnce(status("updating"))
      .mockResolvedValueOnce(status("up_to_date"));

    const { result } = renderHook(() => useIndexStatus("A:/repo"), { wrapper });

    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(result.current.data?.state).toBe("updating");

    await act(() => vi.advanceTimersByTimeAsync(INDEX_STATUS_POLL_MS));
    await act(() => vi.advanceTimersByTimeAsync(10)); // React Query notifies on a timer
    expect(result.current.data?.state).toBe("up_to_date");

    await act(() => vi.advanceTimersByTimeAsync(INDEX_STATUS_POLL_MS * 3));
    expect(mocks.indexStatus).toHaveBeenCalledTimes(2);
  });

  it("is never served from the cache as fresh", async () => {
    mocks.indexStatus.mockResolvedValue(status("up_to_date"));

    const { result } = renderHook(() => useIndexStatus("A:/repo"), { wrapper });
    await act(() => vi.advanceTimersByTimeAsync(0));

    expect(result.current.isStale).toBe(true);
  });
});
