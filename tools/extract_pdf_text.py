"""Extract text from a PDF into a UTF-8 text file."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    document = fitz.open(args.pdf)
    text = "\n\n".join(page.get_text() for page in document)
    args.output.write_text(text, encoding="utf-8")
    print(f"{len(document)} pages -> {args.output}")


if __name__ == "__main__":
    main()
