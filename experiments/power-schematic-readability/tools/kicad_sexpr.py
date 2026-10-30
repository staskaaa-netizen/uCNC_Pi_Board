"""Small, dependency-free helpers for the KiCad S-expression experiment."""

from __future__ import annotations

import re
from pathlib import Path


TOKEN_RE = re.compile(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+')


def parse(text: str):
    tokens = TOKEN_RE.findall(text)
    position = 0

    def read():
        nonlocal position
        token = tokens[position]
        position += 1
        if token == "(":
            result = []
            while tokens[position] != ")":
                result.append(read())
            position += 1
            return result
        if token.startswith('"'):
            return token[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        return token

    return read()


def parse_file(path: Path):
    return parse(path.read_text(encoding="utf-8"))


def children(node: list, name: str) -> list[list]:
    return [
        item
        for item in node
        if isinstance(item, list) and item and item[0] == name
    ]


def child(node: list, name: str):
    matches = children(node, name)
    return matches[0] if matches else None


def property_value(symbol: list, name: str, default: str = "") -> str:
    for prop in children(symbol, "property"):
        if len(prop) >= 3 and prop[1] == name:
            return str(prop[2])
    return default


def number(node: list, name: str, index: int, default: float = 0.0) -> float:
    value = child(node, name)
    if value is None or len(value) <= index:
        return default
    return float(value[index])


def extract_block(text: str, name: str) -> str:
    """Return a balanced top-level block, including its parentheses."""
    match = re.search(rf"(?m)^\s*\({re.escape(name)}\b", text)
    if not match:
        raise ValueError(f"Block not found: {name}")
    start = text.index("(", match.start())
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError(f"Unbalanced block: {name}")


def quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def fmt(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text
