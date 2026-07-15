import { Copy } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";

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
    <div className="space-y-3">
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
    <div className="space-y-2 text-sm leading-6">
      {lines.map((line, index) =>
        line.startsWith("- ") ? (
          <p key={`${line}-${index}`} className="pl-3">
            <span className="text-muted-foreground">- </span>
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
    <div className="overflow-hidden rounded-md border border-border bg-background">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-xs uppercase text-muted-foreground">
          {language || "code"}
        </span>
        <Button
          className="h-7 bg-muted px-2 text-foreground"
          onClick={() => {
            void navigator.clipboard.writeText(code);
            toast.success("Code copied");
          }}
        >
          <Copy className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
          Copy
        </Button>
      </div>
      <pre className="overflow-x-auto p-3 text-xs leading-5">
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
        className="rounded bg-muted px-1 py-0.5 text-xs"
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
      <span key={`${token}-${index}`} className="text-primary">
        {token}
      </span>
    ) : (
      <span key={`${token}-${index}`}>{token}</span>
    ),
  );
}
