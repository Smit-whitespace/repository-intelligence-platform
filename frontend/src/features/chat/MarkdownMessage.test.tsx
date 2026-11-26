import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MarkdownMessage } from "./MarkdownMessage";

describe("MarkdownMessage", () => {
  it("renders bold and italic instead of showing the asterisks", () => {
    const { container } = render(
      <MarkdownMessage content="The **subtotal** is *rounded* to the cent." />,
    );

    expect(screen.getByText("subtotal").tagName).toBe("STRONG");
    expect(screen.getByText("rounded").tagName).toBe("EM");
    expect(container.textContent).not.toContain("*");
  });

  it("renders numbered and bulleted lists with inline formatting", () => {
    const { container } = render(
      <MarkdownMessage
        content={"1. **Subtotal**: sum the lines.\n2. Apply `apply_discount`.\n* A bullet"}
      />,
    );

    expect(screen.getByText("Subtotal").tagName).toBe("STRONG");
    expect(screen.getByText("apply_discount").tagName).toBe("CODE");
    expect(screen.getByText("1.")).toBeInTheDocument();
    expect(screen.getByText("2.")).toBeInTheDocument();
    expect(container.textContent).not.toContain("**");
    expect(container.textContent).not.toMatch(/^\* /m);
  });

  it("renders headings as headings, not '#' text", () => {
    render(<MarkdownMessage content={"## How totals work\nText."} />);

    expect(screen.getByText("How totals work").closest("h4")).not.toBeNull();
    expect(screen.queryByText(/##/)).toBeNull();
  });

  it("does not treat a lone asterisk or code contents as formatting", () => {
    render(<MarkdownMessage content={"Use `a * b * c` and 2 * 3 = 6."} />);

    expect(screen.getByText("a * b * c").tagName).toBe("CODE");
    expect(screen.getByText(/2 \* 3 = 6/)).toBeInTheDocument();
  });

  it("highlights every keyword in a code block", () => {
    // The highlighter used a global regex with .test(), whose lastIndex
    // carried over between calls and skipped every other keyword.
    const { container } = render(
      <MarkdownMessage content={"```python\ndef a():\n    return 1\ndef b():\n    return 2\n```"} />,
    );

    const highlighted = [...container.querySelectorAll("pre span.text-\\[\\#4F8CFF\\]")].map(
      (span) => span.textContent,
    );

    expect(highlighted).toEqual(["def", "return", "def", "return"]);
  });
});
