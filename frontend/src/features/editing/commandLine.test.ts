import { describe, expect, it } from "vitest";
import {
  commandsToText,
  formatCommandLine,
  splitCommandLine,
  textToCommands,
} from "./commandLine";

describe("splitCommandLine", () => {
  it("splits on whitespace and groups quoted text", () => {
    expect(splitCommandLine("pytest -q  'tests/a b.py'")).toEqual([
      "pytest",
      "-q",
      "tests/a b.py",
    ]);
  });

  it("joins quotes with adjacent text", () => {
    expect(splitCommandLine('ruff --config="a b.toml" .')).toEqual([
      "ruff",
      "--config=a b.toml",
      ".",
    ]);
  });

  it("keeps empty arguments and escaped quotes", () => {
    expect(splitCommandLine('cmd "" "say \\"hi\\""')).toEqual([
      "cmd",
      "",
      'say "hi"',
    ]);
  });

  it("leaves Windows paths alone", () => {
    expect(
      splitCommandLine('"C:\\Program Files\\Python\\python.exe" -m pytest'),
    ).toEqual(["C:\\Program Files\\Python\\python.exe", "-m", "pytest"]);
  });
});

describe("formatCommandLine", () => {
  it.each([
    [["pytest", "-q"]],
    [["cmd", "", "a b", 'quote"inside', "it's", "C:\\dir\\"]],
    [["--opt=a b", "x"]],
  ])("round-trips %j", (args) => {
    expect(splitCommandLine(formatCommandLine(args))).toEqual(args);
  });
});

describe("textToCommands", () => {
  it("keeps the name and timeout of unchanged commands", () => {
    const previous = [
      { name: "unit tests", argv: ["pytest", "-q"], timeout_seconds: 900 },
    ];

    const commands = textToCommands(
      `${commandsToText(previous)}\nruff check .`,
      previous,
    );

    expect(commands[0]).toEqual(previous[0]);
    expect(commands[1]).toEqual({
      name: "ruff check",
      argv: ["ruff", "check", "."],
    });
  });

  it("gives every command a unique name", () => {
    const names = textToCommands("ruff check src\nruff check tests").map(
      (command) => command.name,
    );

    expect(names).toEqual(["ruff check", "ruff check (2)"]);
  });

  it("uses the program's file name, not its full path", () => {
    expect(
      textToCommands('"C:\\Tools\\python.exe" check.py')[0].name,
    ).toBe("python.exe check.py");
  });
});
