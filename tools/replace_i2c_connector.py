"""Replace J18 with the project-standard 4-pin 3.5 mm Phoenix connector."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
FOOTPRINT_DIR = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0"
    r"\share\kicad\footprints\Connector_Phoenix_MC.pretty"
)
FOOTPRINT = "PhoenixContact_MCV_1,5_4-G-3.5_1x04_P3.50mm_Vertical"
NETS = {"1": "I2C_SDA", "2": "I2C_SCL", "3": "+3V3", "4": "GND"}
TARGET_POSITION_MM = (186.69, 28.575)
TARGET_ROTATION_DEGREES = 90.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    old = next(
        (
            footprint
            for footprint in board.GetFootprints()
            if footprint.GetReference() == "J18"
        ),
        None,
    )
    if old is None:
        raise SystemExit("J18 not found")
    print(
        f"J18 current footprint: "
        f"{old.GetFPID().GetLibNickname()}:{old.GetFPID().GetLibItemName()}"
    )
    print(f"J18 target footprint: Connector_Phoenix_MC:{FOOTPRINT}")
    if not args.apply:
        return

    replacement = pcbnew.FootprintLoad(str(FOOTPRINT_DIR), FOOTPRINT)
    if replacement is None:
        raise SystemExit("Phoenix 4-pin footprint not found")
    replacement.SetReference(old.GetReference())
    replacement.SetValue(old.GetValue())
    replacement.SetPosition(pcbnew.VECTOR2I_MM(*TARGET_POSITION_MM))
    replacement.SetOrientationDegrees(TARGET_ROTATION_DEGREES)
    replacement.SetLayer(old.GetLayer())
    replacement.SetDNP(old.IsDNP())
    replacement.SetLocked(old.IsLocked())
    replacement.SetPath(old.GetPath())
    replacement.Reference().SetLayer(pcbnew.F_Fab)
    replacement.Value().SetLayer(pcbnew.F_Fab)
    for pad in replacement.Pads():
        target = NETS[pad.GetNumber()]
        net = board.FindNet(target)
        if net is None:
            raise SystemExit(f"Missing net {target}")
        pad.SetNet(net)

    board.Remove(old)
    board.Add(replacement)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
