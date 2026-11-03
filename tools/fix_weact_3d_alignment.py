"""Apply the verified 3D transform to the WeAct module instance."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
SOCKET_STACK_HEIGHT_MM = 8.5
OFFSET_MM = (-20.7, 20.6, SOCKET_STACK_HEIGHT_MM)
SOCKET_MODEL = (
    "${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/"
    "PinSocket_1x15_P2.54mm_Vertical.step"
)
SOCKET_ROWS_Y_MM = (-19.47, -16.93, 16.09, 18.63)
SOCKET_START_X_MM = -19.47


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprint = next(
        (item for item in board.GetFootprints() if item.GetReference() == "MOD1"),
        None,
    )
    if footprint is None:
        raise SystemExit("MOD1 not found")
    models = footprint.Models()
    model = next(
        (item for item in models if str(item.m_Filename).endswith("WeAct_RP2350B.step")),
        None,
    )
    if model is None:
        raise SystemExit("MOD1 WeAct 3D model not found")
    print(
        "before:",
        model.m_Filename,
        model.m_Offset.x,
        model.m_Offset.y,
        model.m_Offset.z,
    )
    model.m_Offset.x, model.m_Offset.y, model.m_Offset.z = OFFSET_MM
    print("after:", model.m_Offset.x, model.m_Offset.y, model.m_Offset.z)
    existing_offsets = {
        (round(float(item.m_Offset.x), 3), round(float(item.m_Offset.y), 3))
        for item in models
        if str(item.m_Filename) == SOCKET_MODEL
    }
    for y in SOCKET_ROWS_Y_MM:
        key = (SOCKET_START_X_MM, y)
        if key in existing_offsets:
            continue
        socket = pcbnew.FP_3DMODEL()
        socket.m_Filename = SOCKET_MODEL
        socket.m_Offset.x = SOCKET_START_X_MM
        socket.m_Offset.y = y
        socket.m_Offset.z = 0.0
        socket.m_Scale.x = 1.0
        socket.m_Scale.y = 1.0
        socket.m_Scale.z = 1.0
        footprint.Add3DModel(socket)
        print("added socket model at", key)
    if not args.apply:
        return
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
