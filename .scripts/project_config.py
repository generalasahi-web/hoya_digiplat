#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return ""
    return value


def load_config(path: Path) -> dict:
    root: dict = {}
    stack: list[tuple[int, dict]] = [(0, root)]

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError(f"Indent must be multiples of 2 spaces: line {lineno}")

        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"Invalid line: {lineno}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()

        current = stack[-1][1]
        if raw_value == "":
            child: dict = {}
            current[key] = child
            stack.append((indent + 2, child))
        else:
            current[key] = parse_scalar(raw_value)

    return root


def get_value(data: dict, dotted_key: str):
    current = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part, "")
    return current


def stringify(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value or "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read simple values from .claude/project.config.yaml")
    parser.add_argument("key")
    parser.add_argument("--config", default=".claude/project.config.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    print(stringify(get_value(config, args.key)))


if __name__ == "__main__":
    main()
