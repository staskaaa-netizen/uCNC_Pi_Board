"""Add the fitted DS90LV047A LCD-LVDS driver and select the active variant."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
SO_DIR = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0"
    r"\share\kicad\footprints\Package_SO.pretty"
)
CAP_DIR = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0"
    r"\share\kicad\footprints\Capacitor_SMD.pretty"
)
DRIVER_NETS = {
    "1": "+3V3",
    "2": "HSTX_CLK_P",
    "3": "HSTX_D2_P",
    "4": "+3V3",
    "5": "GND",
    "6": "HSTX_D1_P",
    "7": "HSTX_D0_P",
    "8": "GND",
    "9": "LVDS_D0_N",
    "10": "LVDS_D0_P",
    "11": "LVDS_D1_P",
    "12": "LVDS_D1_N",
    "13": "LVDS_D2_N",
    "14": "LVDS_D2_P",
    "15": "LVDS_CLK_P",
    "16": "LVDS_CLK_N",
}


def place_driver(board) -> None:
    driver = pcbnew.FootprintLoad(str(SO_DIR), "SOIC-16_3.9x9.9mm_P1.27mm")
    if driver is None:
        raise SystemExit("SOIC-16 footprint not found")
    driver.SetReference("U41")
    driver.SetValue("DS90LV047A")
    driver.SetPosition(pcbnew.VECTOR2I_MM(125.0, 38.0))
    driver.SetOrientationDegrees(0)
    driver.SetLayer(pcbnew.F_Cu)
    driver.Reference().SetLayer(pcbnew.F_Fab)
    driver.Value().SetLayer(pcbnew.F_Fab)
    for pad in driver.Pads():
        pad.SetNet(board.FindNet(DRIVER_NETS[pad.GetNumber()]))
    board.Add(driver)

    bypass = pcbnew.FootprintLoad(
        str(CAP_DIR),
        "C_0805_2012Metric",
    )
    if bypass is None:
        raise SystemExit("0805 capacitor footprint not found")
    bypass.SetReference("C106")
    bypass.SetValue("100nF")
    bypass.SetPosition(pcbnew.VECTOR2I_MM(125.0, 45.0))
    bypass.SetOrientationDegrees(0)
    bypass.SetLayer(pcbnew.F_Cu)
    bypass.Reference().SetLayer(pcbnew.F_Fab)
    bypass.Value().SetLayer(pcbnew.F_Fab)
    bypass.FindPadByNumber("1").SetNet(board.FindNet("+3V3"))
    bypass.FindPadByNumber("2").SetNet(board.FindNet("GND"))
    board.Add(bypass)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if "U41" in footprints:
        print("U41 already present")
        return
    for reference in ("RN26", "RN27"):
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"{reference} not found")
        footprint.SetDNP(True)
    print("U41 at 125.0,38.0; C106 at 125.0,45.0; RN26/RN27 marked DNP")
    if not args.apply:
        return
    place_driver(board)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
