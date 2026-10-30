"""Render the first page of a PDF to PNG for visual review."""

from __future__ import annotations

import argparse
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("png", type=Path)
    parser.add_argument("--zoom", type=float, default=2.0)
    parser.add_argument("--page", type=int, default=1)
    args = parser.parse_args()
    document = pymupdf.open(args.pdf)
    page = document[args.page - 1]
    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(args.zoom, args.zoom),
        colorspace=pymupdf.csRGB,
        alpha=False,
    )
    args.png.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(args.png)
    print(
        {
            "pdf": str(args.pdf),
            "png": str(args.png),
            "pages": document.page_count,
            "width": pixmap.width,
            "height": pixmap.height,
        }
    )


if __name__ == "__main__":
    main()
