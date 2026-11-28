import { describe, expect, it } from "vitest";
import type { FreshnessResult } from "@/types/api";
import { indexingLabel } from "./indexingLabel";

function result(
  state: FreshnessResult["state"],
  changed = 0,
  added = 0,
  removed = 0,
): FreshnessResult {
  return {
    state,
    changed_files: changed,
    added_files: added,
    removed_files: removed,
    updated_files: 0,
    pending_files: changed + added + removed,
    seconds: 0,
    note: null,
  };
}

describe("indexingLabel", () => {
  it("names the states", () => {
    expect(indexingLabel(result("up_to_date"))).toBe("Up to date");
    expect(indexingLabel(result("updated"))).toBe("Up to date");
    expect(indexingLabel(result("updating"))).toBe("Updating");
    expect(indexingLabel(result("not_indexed"))).toBe("Not indexed");
    expect(indexingLabel(result("incompatible"))).toBe(
      "Needs reindex (different embedding model)",
    );
  });

  it("counts changed files as 1 file or N files", () => {
    expect(indexingLabel(result("stale", 1))).toBe("1 file changed since indexing");
    expect(indexingLabel(result("stale", 1, 1, 1))).toBe(
      "3 files changed since indexing",
    );
  });
});
