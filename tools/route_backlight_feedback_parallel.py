"""Route R128 in parallel with R127 on the backlight feedback network."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
TRACK_WIDTH_MM = 0.2
VIA_DIAMETER_MM = 0.6
VIA_DRILL_MM = 0.3


def point_mm(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def add_track(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start_mm: tuple[float, float],
    end_mm: tuple[float, float],
) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I_MM(*start_mm))
    track.SetEnd(pcbnew.VECTOR2I_MM(*end_mm))
    track.SetLayer(pcbnew.B_Cu)
    track.SetWidth(pcbnew.FromMM(TRACK_WIDTH_MM))
    track.SetNet(net)
    board.Add(track)


def add_via(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    position_mm: tuple[float, float],
) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I_MM(*position_mm))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetWidth(pcbnew.FromMM(VIA_DIAMETER_MM))
    via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
    via.SetNet(net)
    board.Add(via)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for reference in ("R127", "R128"):
        if reference not in footprints:
            raise SystemExit(f"{reference} is missing")

    r127_fb = footprints["R127"].FindPadByNumber("1").GetPosition()
    r128_fb = footprints["R128"].FindPadByNumber("1").GetPosition()
    r128_gnd = footprints["R128"].FindPadByNumber("2").GetPosition()
    if footprints["R127"].FindPadByNumber("2").GetNetname() != "GND":
        raise SystemExit("R127 pin 2 is not GND")
    if footprints["R128"].FindPadByNumber("2").GetNetname() != "GND":
        raise SystemExit("R128 pin 2 is not GND")

    start = point_mm(r128_fb)
    end = point_mm(r127_fb)
    fb12 = board.FindNet("FB12")
    gnd = board.FindNet("GND")
    if fb12 is None or gnd is None:
        raise SystemExit("FB12 or GND net is missing")

    via_points = (start, end, point_mm(r128_gnd))
    existing_vias = {
        (round(point_mm(item.GetPosition())[0], 3), round(point_mm(item.GetPosition())[1], 3))
        for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA)
    }
    route = (
        (start, (start[0], 140.0)),
        ((start[0], 140.0), (end[0], 140.0)),
        ((end[0], 140.0), end),
    )
    existing_b_tracks = {
        (point_mm(item.GetStart()), point_mm(item.GetEnd()))
        for item in board.GetTracks()
        if item.GetClass() == "PCB_TRACK" and item.GetLayer() == pcbnew.B_Cu
    }

    if args.apply:
        for point in via_points:
            key = (round(point[0], 3), round(point[1], 3))
            if key not in existing_vias:
                add_via(board, fb12 if point != point_mm(r128_gnd) else gnd, point)
        for start_mm, end_mm in route:
            reverse = (end_mm, start_mm)
            if start_mm not in existing_b_tracks and reverse not in existing_b_tracks:
                add_track(board, fb12, start_mm, end_mm)
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)

    print(f"R127 FB12 pad={end}")
    print(f"R128 FB12 pad={start}")
    print(f"R128 GND pad={point_mm(r128_gnd)}")
    print(f"route={route}")
    print(f"apply={args.apply}")


if __name__ == "__main__":
    main()
