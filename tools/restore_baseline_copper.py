"""Restore baseline copper whose net names still exist in the edited design."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def point_tuple(point) -> tuple[int, int]:
    return (point.x, point.y)


def track_key(track) -> tuple:
    if isinstance(track, pcbnew.PCB_VIA):
        return (
            "via",
            track.GetNetname(),
            point_tuple(track.GetPosition()),
            track.GetWidth(pcbnew.F_Cu),
            track.GetDrillValue(),
            track.TopLayer(),
            track.BottomLayer(),
        )
    return (
        "track",
        track.GetNetname(),
        track.GetLayer(),
        track.GetWidth(),
        point_tuple(track.GetStart()),
        point_tuple(track.GetEnd()),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--baseline-ref", default="HEAD")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--replace-all",
        action="store_true",
        help="Replace all current copper with the active-net baseline copper",
    )
    parser.add_argument(
        "--exclude-net",
        action="append",
        default=[],
        help="Do not restore baseline copper on this net; may be repeated",
    )
    args = parser.parse_args()

    baseline_text = subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "show",
            f"{args.baseline_ref}:hardware/motherboard.kicad_pcb",
        ],
        cwd=ROOT,
    )
    with tempfile.NamedTemporaryFile(
        suffix=".kicad_pcb", delete=False, dir=ROOT / "tmp"
    ) as baseline_file:
        baseline_file.write(baseline_text)
        baseline_path = Path(baseline_file.name)

    try:
        baseline = pcbnew.LoadBoard(str(baseline_path))
        board = pcbnew.LoadBoard(str(args.board))
        baseline_items = list(baseline.GetTracks())
        current_items = list(board.GetTracks())
        existing = {track_key(item) for item in current_items}
        additions = []
        skipped_nets = set()
        excluded_nets = set(args.exclude_net)
        for item in baseline_items:
            net_name = item.GetNetname()
            if net_name in excluded_nets:
                continue
            if not net_name or board.FindNet(net_name) is None:
                if net_name:
                    skipped_nets.add(net_name)
                continue
            if args.replace_all or track_key(item) not in existing:
                additions.append(item)

        print(
            f"baseline_tracks={len(baseline_items)} "
            f"baseline_segments={sum(not isinstance(item, pcbnew.PCB_VIA) for item in baseline_items)} "
            f"baseline_vias={sum(isinstance(item, pcbnew.PCB_VIA) for item in baseline_items)} "
            f"current_tracks={len(current_items)} "
            f"current_segments={sum(not isinstance(item, pcbnew.PCB_VIA) for item in current_items)} "
            f"current_vias={sum(isinstance(item, pcbnew.PCB_VIA) for item in current_items)} "
            f"missing_tracks={len(additions)}"
        )
        print(f"skipped_obsolete_nets={sorted(skipped_nets)}")
        print(f"excluded_nets={sorted(excluded_nets)}")
        if not args.apply:
            return

        if args.replace_all:
            for item in list(board.GetTracks()):
                board.Remove(item)

        for item in additions:
            net = board.FindNet(item.GetNetname())
            if isinstance(item, pcbnew.PCB_VIA):
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(item.GetPosition())
                via.SetWidth(item.GetWidth(pcbnew.F_Cu))
                via.SetDrill(item.GetDrillValue())
                first, second = item.TopLayer(), item.BottomLayer()
                via.SetLayerPair(first, second)
                via.SetNet(net)
                board.Add(via)
            else:
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(item.GetStart())
                track.SetEnd(item.GetEnd())
                track.SetWidth(item.GetWidth())
                track.SetLayer(item.GetLayer())
                track.SetNet(net)
                board.Add(track)

        if not args.replace_all:
            seen_vias = set()
            for item in list(board.GetTracks()):
                if not isinstance(item, pcbnew.PCB_VIA):
                    continue
                key = track_key(item)
                if key in seen_vias:
                    board.Remove(item)
                else:
                    seen_vias.add(key)

        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")
    finally:
        baseline_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
