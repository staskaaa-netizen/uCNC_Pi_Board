"""Apply the shared short naming convention to checked-in KiCad files."""

from __future__ import annotations

from pathlib import Path

from configure_netclasses import configure_netclasses
from design_names import shorten_embedded_text, shorten_quoted_tokens


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"


def rewrite(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(shorten_quoted_tokens(text), encoding="utf-8")


def rewrite_docs() -> None:
    paths = [
        ROOT / "README.md",
        ROOT / "TODO.md",
        *sorted((ROOT / "documentation").glob("*.md")),
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        path.write_text(shorten_embedded_text(text), encoding="utf-8")


def main() -> None:
    for path in sorted(HARDWARE.glob("*.kicad_sch")):
        rewrite(path)
    rewrite(HARDWARE / "motherboard.kicad_pcb")
    configure_netclasses()
    rewrite_docs()
    print("Applied short design names to schematic, PCB and netclass patterns")


if __name__ == "__main__":
    main()
