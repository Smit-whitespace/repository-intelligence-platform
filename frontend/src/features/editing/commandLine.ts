import type { ValidationCommand } from "@/types/api";

/**
 * Split one command line into arguments.
 *
 * A small, predictable subset of shell quoting (nothing is executed by a
 * shell; the result is an argv list):
 * - whitespace separates arguments;
 * - "double quotes" and 'single quotes' group text, and join with
 *   adjacent text, so `--opt="a b"` is one argument `--opt=a b`;
 * - `""` is an empty argument;
 * - inside double quotes, `\"` is a literal quote. Backslashes are
 *   otherwise literal, so Windows paths need no escaping.
 */
export function splitCommandLine(line: string): string[] {
  const args: string[] = [];
  let current = "";
  let inArgument = false;
  let index = 0;

  while (index < line.length) {
    const char = line[index];

    if (/\s/.test(char)) {
      if (inArgument) {
        args.push(current);
        current = "";
        inArgument = false;
      }
      index += 1;
      continue;
    }

    inArgument = true;

    if (char === '"') {
      index += 1;
      while (index < line.length && line[index] !== '"') {
        if (line[index] === "\\" && line[index + 1] === '"') {
          current += '"';
          index += 2;
        } else {
          current += line[index];
          index += 1;
        }
      }
      index += 1;
      continue;
    }

    if (char === "'") {
      const end = line.indexOf("'", index + 1);
      const stop = end === -1 ? line.length : end;
      current += line.slice(index + 1, stop);
      index = stop + 1;
      continue;
    }

    current += char;
    index += 1;
  }

  if (inArgument) {
    args.push(current);
  }

  return args;
}

/** Format arguments so that `splitCommandLine` returns them unchanged. */
export function formatCommandLine(args: string[]): string {
  return args
    .map((arg) =>
      arg === "" || /[\s"']/.test(arg)
        ? `"${arg.replace(/"/g, '\\"')}"`
        : arg,
    )
    .join(" ");
}

export function commandsToText(commands: ValidationCommand[]): string {
  return commands.map((command) => formatCommandLine(command.argv)).join("\n");
}

/**
 * Turn edited text back into commands.
 *
 * A line whose arguments are unchanged keeps its previous name and
 * timeout; new lines get a unique name based on their first arguments.
 */
export function textToCommands(
  text: string,
  previous: ValidationCommand[] = [],
): ValidationCommand[] {
  const byArgv = new Map(
    previous.map((command) => [JSON.stringify(command.argv), command]),
  );
  const usedNames = new Set<string>();

  return text
    .split("\n")
    .map((line) => splitCommandLine(line))
    .filter((argv) => argv.length > 0)
    .map((argv) => {
      const existing = byArgv.get(JSON.stringify(argv));
      const base =
        existing?.name ??
        [baseName(argv[0]), ...argv.slice(1, 2)].join(" ");

      let name = base;
      for (let suffix = 2; usedNames.has(name); suffix += 1) {
        name = `${base} (${suffix})`;
      }
      usedNames.add(name);

      return existing
        ? { ...existing, name }
        : {
            name,
            argv,
          };
    });
}

function baseName(program: string): string {
  return program.split(/[\\/]/).pop() || program;
}
