"""Apply configured netclass widths to existing PCB track segments."""

from __future__ import annotations

import argparse
import fnmatch
import json
from collections import Counter
from pathlib import Path

import pcbnew

from configure_netclasses import CLASSES, PATTERNS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_REPORT = ROOT / "tmp" / "netclass-track-widths.json"
CLASS_WIDTHS = {
    item["name"]: pcbnew.FromMM(item["track_width"])
    for item in CLASSES
}


def class_for_net(net_name: str) -> str:
    for netclass, pattern in PATTERNS:
        if fnmatch.fnmatchcase(net_name, pattern):
            return netclass
    return "Default"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    changes = []
    before = Counter()
    after = Counter()
    by_net = Counter()
    for track in board.GetTracks():
        if track.GetClass() != "PCB_TRACK":
            continue
        net_name = track.GetNetname()
        netclass = class_for_net(net_name)
        desired = CLASS_WIDTHS[netclass]
        current = track.GetWidth()
        before[(netclass, round(pcbnew.ToMM(current), 3))] += 1
        after[(netclass, round(pcbnew.ToMM(desired), 3))] += 1
        if desired != current:
            changes.append((net_name, netclass, current, desired))
            by_net[net_name] += 1
            if args.apply:
                track.SetWidth(desired)

    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)

    report = {
        "board": str(args.board),
        "apply": args.apply,
        "track_segments_changed": len(changes),
        "nets_changed": len(by_net),
        "before_by_class_and_width": [
            {
                "netclass": netclass,
                "width_mm": width,
                "segments": count,
            }
            for (netclass, width), count in sorted(before.items())
        ],
        "after_by_class_and_width": [
            {
                "netclass": netclass,
                "width_mm": width,
                "segments": count,
            }
            for (netclass, width), count in sorted(after.items())
        ],
        "changed_segments_by_net": dict(sorted(by_net.items())),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
