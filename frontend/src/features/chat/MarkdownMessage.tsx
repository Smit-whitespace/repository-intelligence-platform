import { Copy } from "lucide-react";
import { toast } from "sonner";

type MarkdownMessageProps = {
  content: string;
};

type Segment =
  | {
      type: "code";
      language: string;
      content: string;
    }
  | {
      type: "text";
      content: string;
    };

export function MarkdownMessage({ content }: MarkdownMessageProps) {
  const segments = parseMarkdown(content);

  return (
    <div className="space-y-4">
      {segments.map((segment, index) =>
        segment.type === "code" ? (
          <CodeBlock
            key={`${segment.type}-${index}`}
            code={segment.content}
            language={segment.language}
          />
        ) : (
          <TextBlock key={`${segment.type}-${index}`} content={segment.content} />
        ),
      )}
    </div>
  );
}

function TextBlock({ content }: { content: string }) {
  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return null;
  }

  return (
    <div className="space-y-2 leading-7">
      {lines.map((line, index) =>
        line.startsWith("- ") ? (
          <p key={`${line}-${index}`} className="pl-4">
            <span className="text-[#7A8599]">- </span>
            {renderInline(line.slice(2))}
          </p>
        ) : (
          <p key={`${line}-${index}`}>{renderInline(line)}</p>
        ),
      )}
    </div>
  );
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  return (
    <div className="overflow-hidden rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.06)] bg-[#0A0F1E]">
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] bg-[#111827] px-4 py-2">
        <span className="text-xs font-medium text-[#7A8599]">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={() => {
            void navigator.clipboard.writeText(code);
            toast.success("Code copied");
          }}
          className="flex items-center gap-1.5 rounded-[4px] px-2 py-1 text-xs text-[#7A8599] transition hover:bg-[rgba(255,255,255,0.06)] hover:text-[#F8FAFC]"
        >
          <Copy className="h-3 w-3" />
          Copy
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-6">
        <code>{highlightCode(code)}</code>
      </pre>
    </div>
  );
}

function parseMarkdown(content: string): Segment[] {
  const segments: Segment[] = [];
  const fence = /```(\w+)?\n([\s\S]*?)```/g;
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = fence.exec(content))) {
    if (match.index > cursor) {
      segments.push({
        type: "text",
        content: content.slice(cursor, match.index),
      });
    }

    segments.push({
      type: "code",
      language: match[1] ?? "",
      content: match[2].trimEnd(),
    });
    cursor = match.index + match[0].length;
  }

  if (cursor < content.length) {
    segments.push({
      type: "text",
      content: content.slice(cursor),
    });
  }

  return segments.length
    ? segments
    : [
        {
          type: "text",
          content,
        },
      ];
}

function renderInline(line: string) {
  const parts = line.split(/(`[^`]+`)/g);

  return parts.map((part, index) =>
    part.startsWith("`") && part.endsWith("`") ? (
      <code
        key={`${part}-${index}`}
        className="rounded bg-[rgba(79,140,255,0.1)] px-1.5 py-0.5 text-xs font-mono text-[#22D3EE]"
      >
        {part.slice(1, -1)}
      </code>
    ) : (
      <span key={`${part}-${index}`}>{part}</span>
    ),
  );
}

function highlightCode(code: string) {
  const keywordPattern =
    /\b(const|let|var|function|return|if|else|for|while|class|def|import|from|type|interface|export|async|await|try|catch|except|true|false|null|None)\b/g;
  const tokens = code.split(keywordPattern);

  return tokens.map((token, index) =>
    keywordPattern.test(token) ? (
      <span key={`${token}-${index}`} className="text-[#4F8CFF]">
        {token}
      </span>
    ) : (
      <span key={`${token}-${index}`}>{token}</span>
    ),
  );
}
