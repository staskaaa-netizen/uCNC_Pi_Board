"""Combine the two one-page results into one comparison PDF."""

from __future__ import annotations

import argparse
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path)
    parser.add_argument("--second", type=Path)
    parser.add_argument("--inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    sources = args.inputs or [args.first, args.second]
    if not all(sources):
        parser.error("provide --inputs or both --first and --second")
    output = pymupdf.open()
    for source in sources:
        document = pymupdf.open(source)
        output.insert_pdf(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.save(args.output, garbage=4, deflate=True)
    print({"output": str(args.output), "pages": output.page_count})


if __name__ == "__main__":
    main()
