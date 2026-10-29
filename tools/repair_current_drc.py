"""Repair current-board opens, orphan stubs, and blocked thermal pads.

This deliberately does not move footprints or delete existing routed nets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

REMOVE_UUIDS = {
    # Zero-length branches left at junctions or immediately past end points.
    "5db1c2de-5212-4cf8-ae4d-76de620a2cf5",
    "f937b0d7-af69-4d9b-83d1-2c24997e2ff8",
    "e6dad447-6b46-4b1e-b21f-c3ecc4d3a965",
    "a8ebdddb-e492-4875-8c46-2e0ecc9ae661",
    # Extra through-via with copper on one side only.
    "edc96841-f399-4366-a8a1-86ad6efc8953",
}

REMOVE_VIAS_AT = {
    # A proposed U7 stitch was not safe next to the B.Cu shift-register routes.
    (69.675, 59.975),
    # KiCad assigned this proposed stitch to the nearby EXP_IN3 track.
    (68.85, 59.975),
}

FULL_ZONE_PADS = {
    ("U7", "15"),
    ("U25", "19"),
    # These pads currently have only one thermal spoke.
    ("U24", "19"),
    ("U8", "8"),
    ("U1", "8"),
}

TRACKS = (
    # Isolated-input ground branches to the existing local ISO_GND bus.
    (("U20", "4"), (43.175, 75.365), "ISO_GND", 0.2, pcbnew.F_Cu),
    (("U20", "6"), (43.175, 77.905), "ISO_GND", 0.2, pcbnew.F_Cu),
    (("U20", "8"), (43.175, 80.445), "ISO_GND", 0.2, pcbnew.F_Cu),
    (("U21", "8"), (43.175, 94.945), "ISO_GND", 0.2, pcbnew.F_Cu),
    # FB2's input pad crosses to the existing +3V3 trunk on B.Cu.
    (("FB2", "1"), (163.45, 85.7875), "+3V3", 0.8, pcbnew.F_Cu),
    # Complete the short FB5_TOP link between its two parallel resistors.
    (("R71", "1"), (194.7, 121.8625), "FB5_TOP", 0.2, pcbnew.F_Cu),
)

VIAS = (
    ((163.45, 85.7875), "+3V3", 0.8, 0.4),
    # Stitch the largest otherwise floating F.Cu GND island in the power area.
    ((129.0, 112.0), "GND", 0.6, 0.3),
    ((160.0, 110.0), "GND", 0.6, 0.3),
    # U7.15 sits on a small F.Cu island between two angled signals.
    ((69.675, 60.775), "GND", 0.5, 0.3),
)


def find_pad(board: pcbnew.BOARD, reference: str, pin: str):
    footprint = next(
        (
            item
            for item in board.GetFootprints()
            if item.GetReference() == reference
        ),
        None,
    )
    if footprint is None:
        raise RuntimeError(f"Footprint not found: {reference}")
    pad = footprint.FindPadByNumber(pin)
    if pad is None:
        raise RuntimeError(f"Pad not found: {reference}.{pin}")
    return pad


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    required_pads = {
        (reference, pin): find_pad(board, reference, pin)
        for (reference, pin), *_ in TRACKS
    }
    zone_pads = {
        (reference, pin): find_pad(board, reference, pin)
        for reference, pin in FULL_ZONE_PADS
    }

    added_tracks = []
    for (reference, pin), end, expected_net, width, layer in TRACKS:
        pad = required_pads[(reference, pin)]
        if pad.GetNetname() != expected_net:
            raise RuntimeError(
                f"{reference}.{pin} is on {pad.GetNetname()}, expected {expected_net}"
            )
        start = (
            pcbnew.ToMM(pad.GetPosition().x),
            pcbnew.ToMM(pad.GetPosition().y),
        )
        existing = any(
            item.GetClass() == "PCB_TRACK"
            and item.GetLayer() == layer
            and item.GetNetname() == expected_net
            and {
                (
                    round(pcbnew.ToMM(item.GetStart().x), 4),
                    round(pcbnew.ToMM(item.GetStart().y), 4),
                ),
                (
                    round(pcbnew.ToMM(item.GetEnd().x), 4),
                    round(pcbnew.ToMM(item.GetEnd().y), 4),
                ),
            }
            == {
                (round(start[0], 4), round(start[1], 4)),
                (round(end[0], 4), round(end[1], 4)),
            }
            for item in board.GetTracks()
        )
        if not existing:
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(pad.GetPosition())
            track.SetEnd(pcbnew.VECTOR2I_MM(*end))
            track.SetWidth(pcbnew.FromMM(width))
            track.SetLayer(layer)
            track.SetNet(pad.GetNet())
            board.Add(track)
            added_tracks.append(f"{reference}.{pin}->{end}")

    added_vias = []
    for position, net_name, diameter, drill in VIAS:
        net = board.FindNet(net_name)
        if net is None:
            raise RuntimeError(f"Net not found: {net_name}")
        if any(
            isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname() == net_name
            and abs(pcbnew.ToMM(item.GetPosition().x) - position[0]) < 0.0001
            and abs(pcbnew.ToMM(item.GetPosition().y) - position[1]) < 0.0001
            for item in board.GetTracks()
        ):
            continue
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I_MM(*position))
        via.SetWidth(pcbnew.FromMM(diameter))
        via.SetDrill(pcbnew.FromMM(drill))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(net)
        board.Add(via)
        added_vias.append(f"{net_name}@{position}")

    changed_pads = []
    for reference, pin in sorted(FULL_ZONE_PADS):
        pad = zone_pads[(reference, pin)]
        pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        changed_pads.append(f"{reference}.{pin}")

    removed = []
    for item in list(board.GetTracks()):
        remove = item.m_Uuid.AsString() in REMOVE_UUIDS
        if isinstance(item, pcbnew.PCB_VIA):
            remove = remove or any(
                abs(pcbnew.ToMM(item.GetPosition().x) - x) < 0.0001
                and abs(pcbnew.ToMM(item.GetPosition().y) - y) < 0.0001
                for x, y in REMOVE_VIAS_AT
            )
        if remove:
            removed.append(item.m_Uuid.AsString())
            board.Remove(item)

    board.BuildConnectivity()
    print(f"removed={len(removed)} added_tracks={len(added_tracks)} "
          f"added_vias={len(added_vias)} direct_zone_pads={len(changed_pads)}")
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
