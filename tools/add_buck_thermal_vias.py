"""Add the six-via thermal arrays under the two LMR36510 PowerPADs."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
REGULATORS = ("U1", "U3")
LOCAL_GROUND_PADS = {
    "U2": "1",
    "U34": "1",
    "U37": "2",
}
VIA_DRILL_MM = 0.3
VIA_DIAMETER_MM = 0.6
OFFSETS_MM = (
    (-0.6, -1.0), (0.6, -1.0),
    (-0.6, 0.0), (0.6, 0.0),
    (-0.6, 1.0), (0.6, 1.0),
)


def same_point(
    lhs: pcbnew.VECTOR2I,
    rhs: pcbnew.VECTOR2I,
    tolerance_mm: float = 0.01,
) -> bool:
    return (
        abs(pcbnew.ToMM(lhs.x - rhs.x)) <= tolerance_mm
        and abs(pcbnew.ToMM(lhs.y - rhs.y)) <= tolerance_mm
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    ground = board.FindNet("GND")
    if ground is None:
        raise SystemExit("Board has no GND net")

    added = []
    existing_count = {}
    for reference in REGULATORS:
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"{reference} is missing")
        exposed_pad = footprint.FindPadByNumber("9")
        if exposed_pad is None or exposed_pad.GetNetname() != "GND":
            raise SystemExit(f"{reference} pin 9 is not the GND PowerPAD")
        if exposed_pad.GetPosition() != footprint.GetPosition():
            raise SystemExit(f"{reference} PowerPAD is not centered as expected")

        center = footprint.GetPosition()
        angle = math.radians(footprint.GetOrientationDegrees())
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        found = 0
        for dx, dy in OFFSETS_MM:
            position = pcbnew.VECTOR2I(
                center.x + pcbnew.FromMM(dx * cos_angle - dy * sin_angle),
                center.y + pcbnew.FromMM(dx * sin_angle + dy * cos_angle),
            )
            if any(
                isinstance(item, pcbnew.PCB_VIA)
                and item.GetNetname() == "GND"
                and same_point(item.GetPosition(), position)
                for item in board.GetTracks()
            ):
                found += 1
                continue

            if args.apply:
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(position)
                via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
                via.SetWidth(pcbnew.FromMM(VIA_DIAMETER_MM))
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                via.SetNet(ground)
                board.Add(via)
            added.append((reference, pcbnew.ToMM(position)))
        existing_count[reference] = found

    local_ground_added = []
    for reference, pin in LOCAL_GROUND_PADS.items():
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"{reference} is missing")
        pad = footprint.FindPadByNumber(pin)
        if pad is None or pad.GetNetname() != "GND":
            raise SystemExit(f"{reference} pin {pin} is not GND")
        if any(
            isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname() == "GND"
            and pad.HitTest(item.GetPosition())
            for item in board.GetTracks()
        ):
            continue
        if args.apply:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pad.GetPosition())
            via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
            via.SetWidth(pcbnew.FromMM(VIA_DIAMETER_MM))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(ground)
            board.Add(via)
        local_ground_added.append((reference, pin, pcbnew.ToMM(pad.GetPosition())))

    print(f"existing_thermal_vias={existing_count}")
    print(f"missing_vias={len(added)} {added}")
    print(f"missing_local_ground_vias={local_ground_added}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
