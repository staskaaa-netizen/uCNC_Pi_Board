"""Use solid zone connections except on the two switching regulators."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
THERMAL_REFS = {"U1", "U3"}
PLANED_NETS = {"GND", "PLC_0V"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {
        footprint.GetReference(): footprint
        for footprint in board.GetFootprints()
    }
    changes = []
    for zone in board.Zones():
        if zone.GetPadConnection() != pcbnew.ZONE_CONNECTION_FULL:
            changes.append((f"zone:{zone.GetNetname()}", "FULL"))
            zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

    for reference, footprint in footprints.items():
        for pad in footprint.Pads():
            if pad.GetNetname() not in PLANED_NETS:
                continue
            connection = (
                pcbnew.ZONE_CONNECTION_THERMAL
                if reference in THERMAL_REFS
                else pcbnew.ZONE_CONNECTION_FULL
            )
            if pad.GetLocalZoneConnection() != connection:
                changes.append((reference, pad.GetNumber()))
                pad.SetLocalZoneConnection(connection)

    print(f"solid_connections={sorted(changes)}")
    if not args.apply:
        return
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")


if __name__ == "__main__":
    main()
