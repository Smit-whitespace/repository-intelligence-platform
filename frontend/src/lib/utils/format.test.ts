import { describe, expect, it } from "vitest";
import { formatCount } from "./format";

describe("formatCount", () => {
  it("uses the singular for one and the plural otherwise", () => {
    expect(formatCount(1, "file")).toBe("1 file");
    expect(formatCount(0, "file")).toBe("0 files");
    expect(formatCount(3, "file")).toBe("3 files");
  });
});
