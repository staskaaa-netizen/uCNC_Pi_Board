"""Render front/back placement checkpoints with ratsnest airwires."""

from __future__ import annotations

import argparse
import math
import os
from collections import defaultdict
from pathlib import Path

import pcbnew
import wx


ANCHORS = {
    *{f"J{index}" for index in range(1, 27)},
    "MOD1",
    "SW1",
    "SW2",
    "H1",
    "H2",
    "H3",
    "H4",
}


def net_color(name: str):
    if name.startswith(("ESTOP", "HOLD", "START")):
        return wx.Colour(210, 30, 30)
    if name.startswith(("HDMI_", "HSTX_", "LVDS_")):
        return wx.Colour(160, 30, 180)
    if name.startswith(("SR_", "ENC")):
        return wx.Colour(0, 125, 120)
    if name.startswith(("VIN", "BUCK", "MODULE_5V")) or name.startswith("+"):
        return wx.Colour(70, 120, 190)
    return wx.Colour(105, 105, 105)


def mst_edges(points):
    if len(points) < 2:
        return []
    remaining = set(range(1, len(points)))
    visited = {0}
    edges = []
    while remaining:
        best = None
        for i in visited:
            for j in remaining:
                dx = points[i][0] - points[j][0]
                dy = points[i][1] - points[j][1]
                value = math.hypot(dx, dy)
                if best is None or value < best[0]:
                    best = (value, i, j)
        _, i, j = best
        edges.append((points[i], points[j]))
        visited.add(j)
        remaining.remove(j)
    return edges


def render(
    board_path: Path,
    output_dir: Path,
    checkpoint: str,
    inside_only: bool = False,
) -> None:
    board = pcbnew.LoadBoard(str(board_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    margin_px = 90
    board_w = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetWidth())
    board_h = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetHeight())
    width_px = 2000
    scale = (width_px - 2 * margin_px) / board_w
    height_px = int(board_h * scale + 2 * margin_px)
    origin_x = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetLeft())
    origin_y = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetTop())

    def on_board(footprint) -> bool:
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        return (
            origin_x <= x <= origin_x + board_w
            and origin_y <= y <= origin_y + board_h
        )

    def xy(x: float, y: float):
        return (
            int(round(margin_px + (x - origin_x) * scale)),
            int(round(margin_px + (y - origin_y) * scale)),
        )

    pads_by_net = defaultdict(list)
    components = []
    for footprint in board.GetFootprints():
        if inside_only and not on_board(footprint):
            continue
        both = any(
            pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
            for pad in footprint.Pads()
        )
        side = "THT" if both else ("F" if footprint.GetLayer() == pcbnew.F_Cu else "B")
        components.append((footprint, side))
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            point = pad.GetPosition()
            pad_side = "THT" if both else side
            pads_by_net[net].append(
                (footprint.GetReference(), pcbnew.ToMM(point.x), pcbnew.ToMM(point.y), pad_side)
            )

    airwires = []
    for net, pads in pads_by_net.items():
        if net in {"GND", "PGND", "AGND"} or len(pads) < 2:
            continue
        coords = [(x, y) for _, x, y, _ in pads]
        for a, b in mst_edges(coords):
            a_sides = {side for _, x, y, side in pads if (x, y) == a}
            b_sides = {side for _, x, y, side in pads if (x, y) == b}
            mixed = ("F" in a_sides and "B" in b_sides) or ("B" in a_sides and "F" in b_sides)
            airwires.append((net, a, b, a_sides | b_sides, mixed))

    for side_code, layer, title, body_colour in (
        ("F", pcbnew.F_Cu, "FRONT - F.Cu", wx.Colour(226, 239, 252)),
        ("B", pcbnew.B_Cu, "BACK - B.Cu (board-coordinate view)", wx.Colour(255, 238, 218)),
    ):
        bitmap = wx.Bitmap(width_px, height_px)
        dc = wx.MemoryDC(bitmap)
        dc.SetBackground(wx.Brush(wx.Colour(250, 250, 247)))
        dc.Clear()

        x0, y0 = xy(origin_x, origin_y)
        x1, y1 = xy(origin_x + board_w, origin_y + board_h)
        dc.SetPen(wx.Pen(wx.Colour(30, 30, 30), 3))
        dc.SetBrush(wx.Brush(wx.Colour(247, 249, 245)))
        dc.DrawRectangle(x0, y0, x1 - x0, y1 - y0)

        # 10 mm reference grid.
        dc.SetPen(wx.Pen(wx.Colour(225, 225, 220), 1))
        for x in range(10, int(board_w), 10):
            px, _ = xy(origin_x + x, origin_y)
            dc.DrawLine(px, y0, px, y1)
        for y in range(10, int(board_h), 10):
            _, py = xy(origin_x, origin_y + y)
            dc.DrawLine(x0, py, x1, py)

        for net, a, b, sides, mixed in airwires:
            if side_code == "F" and not ({"F", "THT"} & sides):
                continue
            if side_code == "B" and not ({"B", "THT"} & sides):
                continue
            pen = wx.Pen(net_color(net), 2 if mixed else 1, wx.PENSTYLE_SHORT_DASH if mixed else wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            dc.DrawLine(*xy(*a), *xy(*b))

        for track in board.GetTracks():
            if isinstance(track, pcbnew.PCB_VIA) or not track.IsOnLayer(layer):
                continue
            start = track.GetStart()
            end = track.GetEnd()
            dc.SetPen(
                wx.Pen(
                    net_color(track.GetNetname()),
                    max(2, int(round(pcbnew.ToMM(track.GetWidth()) * scale))),
                )
            )
            dc.DrawLine(
                *xy(pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)),
                *xy(pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)),
            )

        visible = []
        for footprint, component_side in components:
            if component_side not in {"THT", side_code}:
                continue
            visible.append(footprint)

        for footprint in visible:
            ref = footprint.GetReference()
            courtyard_layer = pcbnew.B_CrtYd if layer == pcbnew.B_Cu else pcbnew.F_CrtYd
            courtyard = footprint.GetCourtyard(courtyard_layer)
            box = courtyard.BBox() if courtyard.OutlineCount() else footprint.GetBoundingBox(False, False)
            left, top = xy(pcbnew.ToMM(box.GetLeft()), pcbnew.ToMM(box.GetTop()))
            right, bottom = xy(pcbnew.ToMM(box.GetRight()), pcbnew.ToMM(box.GetBottom()))
            is_anchor = ref in ANCHORS
            if is_anchor:
                fill = wx.Colour(250, 205, 205)
                pen = wx.Pen(wx.Colour(180, 20, 20), 3)
            elif footprint.GetReference().startswith("U"):
                fill = wx.Colour(205, 225, 245) if side_code == "F" else wx.Colour(250, 215, 180)
                pen = wx.Pen(wx.Colour(50, 70, 100), 2)
            else:
                fill = body_colour
                pen = wx.Pen(wx.Colour(120, 120, 120), 1)
            dc.SetPen(pen)
            dc.SetBrush(wx.Brush(fill))
            dc.DrawRectangle(left, top, max(2, right - left), max(2, bottom - top))

            for pad in footprint.Pads():
                if not pad.IsOnLayer(layer):
                    continue
                pb = pad.GetBoundingBox()
                pl, pt = xy(pcbnew.ToMM(pb.GetLeft()), pcbnew.ToMM(pb.GetTop()))
                pr, pbot = xy(pcbnew.ToMM(pb.GetRight()), pcbnew.ToMM(pb.GetBottom()))
                dc.SetPen(wx.Pen(wx.Colour(20, 20, 20), 1))
                dc.SetBrush(wx.Brush(wx.Colour(212, 170, 70) if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else wx.Colour(170, 170, 170)))
                dc.DrawEllipse(pl, pt, max(2, pr - pl), max(2, pbot - pt))

            if is_anchor or ref.startswith(("U", "RN", "MOD")):
                dc.SetTextForeground(wx.Colour(25, 25, 25))
                dc.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                dc.DrawText(ref, left, max(y0, top - 13))

        dc.SetTextForeground(wx.Colour(20, 20, 20))
        dc.SetFont(wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dc.DrawText(f"{checkpoint}: {title}", x0, 28)
        dc.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.DrawText(
            "Red outlines = fixed mechanical anchors. Dashed airwires cross front/back.",
            x0,
            y1 + 16,
        )

        dc.SelectObject(wx.NullBitmap)
        target = output_dir / f"{checkpoint}-{'front' if side_code == 'F' else 'back'}.png"
        bitmap.SaveFile(str(target), wx.BITMAP_TYPE_PNG)
        print(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument(
        "--inside-only",
        action="store_true",
        help="Hide footprints and airwires belonging to components parked off-board",
    )
    args = parser.parse_args()
    app = wx.App(False)
    render(args.board, args.outdir, args.checkpoint, args.inside_only)
    os._exit(0)


if __name__ == "__main__":
    main()
