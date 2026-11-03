"""Add the six-via thermal arrays under the two LMR36510 PowerPADs."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
REGULATORS = {
    "U1": "GND",
    "U3": "PLC_0V",
}
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


def ensure_isolated_back_plane(board, apply: bool) -> bool:
    """Mirror the local F.Cu PLC_0V region under the isolated converter."""
    isolated_net = board.FindNet("PLC_0V")
    if isolated_net is None:
        raise SystemExit("Board has no PLC_0V net")
    if any(
        zone.GetNetname() == "PLC_0V" and zone.IsOnLayer(pcbnew.B_Cu)
        for zone in board.Zones()
    ):
        return False

    source = next(
        (
            zone
            for zone in board.Zones()
            if zone.GetNetname() == "PLC_0V" and zone.IsOnLayer(pcbnew.F_Cu)
        ),
        None,
    )
    if source is None:
        raise SystemExit("Board has no F.Cu PLC_0V source region")

    if apply:
        zone = pcbnew.ZONE(board)
        zone.SetLayer(pcbnew.B_Cu)
        zone.SetNet(isolated_net)
        zone.SetAssignedPriority(3)
        zone.SetOutline(source.Outline())
        board.Add(zone)
    return True


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
    logic_ground = board.FindNet("GND")
    if logic_ground is None:
        raise SystemExit("Board has no GND net")
    missing_isolated_back_plane = ensure_isolated_back_plane(board, args.apply)

    added = []
    existing_count = {}
    for reference, return_net_name in REGULATORS.items():
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"{reference} is missing")
        exposed_pad = footprint.FindPadByNumber("9")
        if exposed_pad is None or exposed_pad.GetNetname() != return_net_name:
            raise SystemExit(
                f"{reference} pin 9 is not the {return_net_name} PowerPAD"
            )
        if exposed_pad.GetPosition() != footprint.GetPosition():
            raise SystemExit(f"{reference} PowerPAD is not centered as expected")
        return_net = board.FindNet(return_net_name)
        if return_net is None:
            raise SystemExit(f"Board has no {return_net_name} net")

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
                and item.GetNetname() == return_net_name
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
                via.SetNet(return_net)
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
            via.SetNet(logic_ground)
            board.Add(via)
        local_ground_added.append((reference, pin, pcbnew.ToMM(pad.GetPosition())))

    print(f"existing_thermal_vias={existing_count}")
    print(f"missing_vias={len(added)} {added}")
    print(f"missing_local_ground_vias={local_ground_added}")
    print(f"missing_isolated_back_plane={missing_isolated_back_plane}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
