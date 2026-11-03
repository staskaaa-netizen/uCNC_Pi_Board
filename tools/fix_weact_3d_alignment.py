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
SOCKET_5_MODEL = (
    "${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/"
    "PinSocket_1x05_P2.54mm_Vertical.step"
)
SOCKET_ROWS_Y_MM = (-19.47, -16.93, 16.09, 18.63)
SOCKET_START_X_MM = -19.47
SOCKET_ROW_ROTATION_Z_DEG = 270.0
SOCKET_5_OFFSET_MM = (9.74, 3.89, 0.0)


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
    row_models = sorted(
        (
            index
            for index, item in enumerate(models)
            if str(item.m_Filename) == SOCKET_MODEL
        ),
        key=lambda index: float(models[index].m_Offset.y),
    )
    for y in SOCKET_ROWS_Y_MM[len(row_models) :]:
        socket = pcbnew.FP_3DMODEL()
        socket.m_Filename = SOCKET_MODEL
        socket.m_Scale.x = 1.0
        socket.m_Scale.y = 1.0
        socket.m_Scale.z = 1.0
        socket.m_Offset.x = SOCKET_START_X_MM
        socket.m_Offset.y = y
        socket.m_Offset.z = 0.0
        socket.m_Rotation.z = SOCKET_ROW_ROTATION_Z_DEG
        footprint.Add3DModel(socket)
        models = footprint.Models()
        row_models.append(len(models) - 1)
    if len(row_models) != len(SOCKET_ROWS_Y_MM):
        raise SystemExit(f"Expected four 1x15 socket models, found {len(row_models)}")
    for model_index, row_y in zip(row_models, SOCKET_ROWS_Y_MM):
        model = models[model_index]
        model.m_Offset.x = SOCKET_START_X_MM
        model.m_Offset.y = row_y
        model.m_Offset.z = 0.0
        model.m_Rotation.z = SOCKET_ROW_ROTATION_Z_DEG
        print("aligned 1x15 socket row at", SOCKET_START_X_MM, row_y)

    five_pin_index = next(
        (
            index
            for index, item in enumerate(models)
            if str(item.m_Filename) == SOCKET_5_MODEL
        ),
        None,
    )
    if five_pin_index is None:
        five_pin_model = pcbnew.FP_3DMODEL()
        five_pin_model.m_Filename = SOCKET_5_MODEL
        five_pin_model.m_Scale.x = 1.0
        five_pin_model.m_Scale.y = 1.0
        five_pin_model.m_Scale.z = 1.0
        five_pin_model.m_Offset.x = SOCKET_5_OFFSET_MM[0]
        five_pin_model.m_Offset.y = SOCKET_5_OFFSET_MM[1]
        five_pin_model.m_Offset.z = SOCKET_5_OFFSET_MM[2]
        footprint.Add3DModel(five_pin_model)
        models = footprint.Models()
        five_pin_index = len(models) - 1
        print("added 1x5 debug socket model")
    five_pin_model = models[five_pin_index]
    five_pin_model.m_Offset.x, five_pin_model.m_Offset.y, five_pin_model.m_Offset.z = SOCKET_5_OFFSET_MM
    five_pin_model.m_Rotation.z = 0.0
    if not args.apply:
        return
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
