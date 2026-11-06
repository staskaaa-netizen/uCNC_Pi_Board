"""Remove F1, bridge its input connection, and exclude D53 from SMT placement."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def endpoint_matches(item, position) -> bool:
    return item.GetStart() == position or item.GetEnd() == position


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    fuse = board.FindFootprintByReference("F1")
    diode = board.FindFootprintByReference("D53")
    if fuse is None:
        raise RuntimeError("F1 not found")
    if diode is None:
        raise RuntimeError("D53 not found")

    fuse_pads = list(fuse.Pads())
    if len(fuse_pads) != 2:
        raise RuntimeError(f"Unexpected F1 pad count: {len(fuse_pads)}")
    start_pad, end_pad = sorted(fuse_pads, key=lambda pad: pad.GetNumber())
    primary_net = start_pad.GetNet()
    secondary_net = end_pad.GetNet()
    start = start_pad.GetPosition()
    end = end_pad.GetPosition()

    bridge_width = max(
        (
            item.GetWidth()
            for item in board.GetTracks()
            if isinstance(item, pcbnew.PCB_TRACK)
            and item.GetNetCode()
            in {primary_net.GetNetCode(), secondary_net.GetNetCode()}
            and (endpoint_matches(item, start) or endpoint_matches(item, end))
        ),
        default=pcbnew.FromMM(0.8),
    )

    print(
        {
            "fuse": "F1",
            "net_merge": f"{secondary_net.GetNetname()} -> {primary_net.GetNetname()}",
            "bridge_mm": [primary_net.GetNetname(), pcbnew.ToMM(bridge_width)],
            "d53_attributes": {
                "before": int(diode.GetAttributes()),
                "after": int(
                    diode.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES
                ),
            },
            "apply": args.apply,
        }
    )
    if not args.apply:
        return

    secondary_code = secondary_net.GetNetCode()
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetCode() == secondary_code:
                pad.SetNet(primary_net)
    for item in board.GetTracks():
        if item.GetNetCode() == secondary_code:
            item.SetNet(primary_net)
    for zone in board.Zones():
        if zone.GetNetCode() == secondary_code:
            zone.SetNet(primary_net)

    board.Remove(fuse)
    bridge = pcbnew.PCB_TRACK(board)
    bridge.SetStart(start)
    bridge.SetEnd(end)
    bridge.SetWidth(bridge_width)
    bridge.SetLayer(pcbnew.F_Cu)
    bridge.SetNet(primary_net)
    board.Add(bridge)

    diode.SetAttributes(
        diode.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES
    )
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Saved {BOARD}")


if __name__ == "__main__":
    main()
