"""Export board artwork, 3D previews and a specification PDF."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_SPEC = ROOT / "documentation" / "board-specification.md"
DEFAULT_OUTPUT = ROOT / "manufacturing"
DEFAULT_KICAD_CLI = (
    Path.home()
    / "AppData"
    / "Local"
    / "Programs"
    / "KiCad"
    / "10.0"
    / "bin"
    / "kicad-cli.exe"
)


def find_kicad_cli(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    discovered = shutil.which("kicad-cli")
    if discovered:
        return Path(discovered)
    if DEFAULT_KICAD_CLI.exists():
        return DEFAULT_KICAD_CLI
    raise SystemExit("kicad-cli was not found; pass --kicad-cli")


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def content_bounds(page: pymupdf.Page) -> pymupdf.Rect:
    rects = [item["rect"] for item in page.get_drawings()]
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                rects.append(pymupdf.Rect(span["bbox"]))
    if not rects:
        return page.rect
    result = pymupdf.Rect(rects[0])
    for rect in rects[1:]:
        result.include_rect(rect)
    return result


def export_layer_pdf(
    kicad_cli: Path,
    board: Path,
    output: Path,
    layers: str,
    title: str,
    mirrored: bool,
    build_dir: Path,
) -> None:
    raw = build_dir / f"{output.stem}-raw.pdf"
    command = [
        str(kicad_cli),
        "pcb",
        "export",
        "pdf",
        "--output",
        str(raw),
        "--layers",
        layers,
        "--mode-single",
        "--scale",
        "1",
        "--check-zones",
    ]
    if mirrored:
        command.append("--mirror")
    command.append(str(board))
    run(command)

    source = pymupdf.open(raw)
    source_page = source[0]
    crop = content_bounds(source_page)
    margin = 12
    crop = pymupdf.Rect(
        crop.x0 - margin,
        crop.y0 - margin,
        crop.x1 + margin,
        crop.y1 + margin,
    ) & source_page.rect
    caption_height = 28
    result = pymupdf.open()
    target = result.new_page(
        width=crop.width,
        height=crop.height + caption_height,
    )
    target.show_pdf_page(
        pymupdf.Rect(0, 0, crop.width, crop.height),
        source,
        0,
        clip=crop,
    )
    target.draw_rect(
        pymupdf.Rect(0, crop.height, crop.width, crop.height + caption_height),
        color=None,
        fill=(0.94, 0.95, 0.96),
    )
    target.insert_text(
        (10, crop.height + 18),
        title,
        fontsize=10,
        fontname="helv",
        color=(0.12, 0.15, 0.19),
    )
    result.set_metadata({"title": title, "creator": "KiCad 10 + PyMuPDF"})
    result.save(output, garbage=4, deflate=True)
    result.close()
    source.close()


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )
    return escaped


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{' '.join(paragraph)}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        if not line:
            flush_paragraph()
            index += 1
            continue
        if line.startswith("```"):
            flush_paragraph()
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            output.append(f"<pre>{html.escape(chr(10).join(code))}</pre>")
            index += 1
            continue
        if line.startswith("|") and "|" in line:
            flush_paragraph()
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                index += 1
            if rows:
                output.append("<table>")
                output.append(
                    "<thead><tr>"
                    + "".join(f"<th>{inline_markup(cell)}</th>" for cell in rows[0])
                    + "</tr></thead>"
                )
                output.append("<tbody>")
                for row in rows[1:]:
                    output.append(
                        "<tr>"
                        + "".join(f"<td>{inline_markup(cell)}</td>" for cell in row)
                        + "</tr>"
                    )
                output.append("</tbody></table>")
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            output.append(
                f"<h{level}>{inline_markup(heading.group(2))}</h{level}>"
            )
            index += 1
            continue
        if line.startswith("- "):
            flush_paragraph()
            items = []
            while index < len(lines) and lines[index].startswith("- "):
                item = lines[index][2:]
                index += 1
                while (
                    index < len(lines)
                    and lines[index].startswith("  ")
                    and lines[index].strip()
                ):
                    item += " " + lines[index].strip()
                    index += 1
                items.append(inline_markup(item))
            output.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
            continue
        paragraph.append(inline_markup(line.strip()))
        index += 1
    flush_paragraph()
    return "\n".join(output)


def export_spec_pdf(spec: Path, output: Path) -> None:
    body = markdown_to_html(spec.read_text(encoding="utf-8"))
    document = f"""<!doctype html>
<html><head><meta charset="utf-8"></head>
<body>{body}</body></html>"""
    css = """
    body { font-family: sans-serif; font-size: 9.5pt; line-height: 1.35;
           color: #1c2430; }
    h1 { font-size: 22pt; color: #16324f; margin: 0 0 10pt 0; }
    h2 { font-size: 13pt; color: #19527a; border-bottom: 1px solid #8aa5b9;
         padding-bottom: 3pt; margin-top: 14pt; margin-bottom: 6pt; }
    h3 { font-size: 11pt; color: #284b63; margin-top: 10pt; }
    p { margin: 4pt 0 6pt 0; }
    ul { margin: 4pt 0 7pt 16pt; padding: 0; }
    li { margin: 2pt 0; }
    table { width: 100%; border-collapse: collapse; margin: 6pt 0 10pt 0;
            font-size: 8.5pt; }
    th { background: #e6edf2; text-align: left; padding: 4pt;
         border: 1px solid #a7b8c5; color: #173b57; }
    td { padding: 3pt 4pt; border: 1px solid #bdcbd5; vertical-align: top; }
    code { font-family: monospace; background: #f1f3f5; }
    """
    story = pymupdf.Story(html=document, user_css=css, em=9.5)
    writer = pymupdf.DocumentWriter(str(output))
    mediabox = pymupdf.paper_rect("a4")
    where = mediabox + (42, 40, -42, -42)
    while True:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
        if not more:
            break
    writer.close()


def export_3d(
    kicad_cli: Path,
    board: Path,
    build_dir: Path,
    side: str,
) -> Path:
    output = build_dir / f"board-3d-{side}.png"
    run(
        [
            str(kicad_cli),
            "pcb",
            "render",
            "--output",
            str(output),
            "--side",
            side,
            "--background",
            "opaque",
            "--quality",
            "high",
            "--floor",
            "--width",
            "1800",
            "--height",
            "1200",
            str(board),
        ]
    )
    return output


def create_review_pdf(
    output: Path,
    front_pdf: Path,
    back_pdf: Path,
    spec_pdf: Path,
    top_image: Path,
    bottom_image: Path,
) -> None:
    review = pymupdf.open()
    cover = review.new_page(width=842, height=595)
    cover.draw_rect(cover.rect, color=None, fill=(0.92, 0.94, 0.96))
    cover.insert_text(
        (36, 48),
        "uCNC RP2350B Motherboard",
        fontsize=24,
        fontname="hebo",
        color=(0.08, 0.19, 0.29),
    )
    cover.insert_text(
        (36, 72),
        "200 x 150 mm | two-layer | 1.6 mm | socketed WeAct RP2350B",
        fontsize=11,
        fontname="helv",
        color=(0.18, 0.29, 0.38),
    )
    image_y = 104
    image_h = 205
    image_w = 370
    cover.insert_text((44, image_y - 8), "TOP ASSEMBLY", fontsize=10, fontname="hebo")
    cover.insert_text((428, image_y - 8), "BOTTOM SIDE", fontsize=10, fontname="hebo")
    cover.insert_image(
        pymupdf.Rect(44, image_y, 44 + image_w, image_y + image_h),
        filename=str(top_image),
        keep_proportion=True,
    )
    cover.insert_image(
        pymupdf.Rect(428, image_y, 428 + image_w, image_y + image_h),
        filename=str(bottom_image),
        keep_proportion=True,
    )
    cover.insert_text(
        (36, 350),
        "Contents: board specification, front artwork and mirrored rear artwork.",
        fontsize=10,
        fontname="helv",
        color=(0.18, 0.29, 0.38),
    )
    cover.insert_text(
        (36, 540),
        "Prototype documentation - not safety certified. Generated from the current KiCad board.",
        fontsize=9,
        fontname="helv",
        color=(0.35, 0.39, 0.43),
    )

    for path in (spec_pdf, front_pdf, back_pdf):
        document = pymupdf.open(path)
        review.insert_pdf(document)
        document.close()

    review.set_metadata(
        {
            "title": "uCNC RP2350B Motherboard Review",
            "subject": "Board specification and manufacturing views",
            "creator": "KiCad 10 + PyMuPDF",
        }
    )
    review.save(output, garbage=4, deflate=True)
    review.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--skip-3d", action="store_true")
    parser.add_argument("--reuse-3d", action="store_true")
    args = parser.parse_args()

    kicad_cli = find_kicad_cli(args.kicad_cli)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    build_root = ROOT / "tmp"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="board-documents-",
        dir=build_root,
    ) as temporary:
        build_dir = Path(temporary)
        front_pdf = args.output_dir / "board-front.pdf"
        back_pdf = args.output_dir / "board-back.pdf"
        spec_pdf = args.output_dir / "board-specification.pdf"
        review_pdf = args.output_dir / "board-review.pdf"

        export_layer_pdf(
            kicad_cli,
            args.board,
            front_pdf,
            "F.Cu,F.Silkscreen,F.Fab,Edge.Cuts",
            "FRONT - F.Cu / F.Silkscreen / F.Fab",
            False,
            build_dir,
        )
        export_layer_pdf(
            kicad_cli,
            args.board,
            back_pdf,
            "B.Cu,B.Silkscreen,B.Fab,Edge.Cuts",
            "BACK - B.Cu / B.Silkscreen / B.Fab (viewed from back)",
            True,
            build_dir,
        )
        export_spec_pdf(args.spec, spec_pdf)

        cached_top = ROOT / "tmp" / "board-3d-top.png"
        cached_bottom = ROOT / "tmp" / "board-3d-bottom.png"
        if args.reuse_3d and cached_top.exists() and cached_bottom.exists():
            top_image = cached_top
            bottom_image = cached_bottom
        elif args.skip_3d:
            top_image = cached_top
            bottom_image = cached_bottom
        else:
            top_image = export_3d(kicad_cli, args.board, build_dir, "top")
            bottom_image = export_3d(kicad_cli, args.board, build_dir, "bottom")

        if top_image.exists() and bottom_image.exists():
            create_review_pdf(
                review_pdf,
                front_pdf,
                back_pdf,
                spec_pdf,
                top_image,
                bottom_image,
            )

        for path in (front_pdf, back_pdf, spec_pdf, review_pdf):
            if path.exists():
                print(f"{path.relative_to(ROOT)}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
