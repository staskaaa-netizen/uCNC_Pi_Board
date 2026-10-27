"""Verify the monotonic U24/U25 -> RN16-RN19 -> motion connector chain."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_REPORT = ROOT / "tmp" / "motion-linear-order.json"
BUFFER_REFS = ("U24", "U25")
RN_REFS = ("RN16", "RN17", "RN18", "RN19")
CONNECTOR_REFS = ("J10", "J11", "J28", "J29", "J30")
PIN_PAIRS = ((1, 8), (2, 7), (3, 6), (4, 5))


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (
        c[0] - a[0]
    )


def crosses(a, b, c, d) -> bool:
    if {a, b} & {c, d}:
        return False
    return (
        orientation(a, b, c) * orientation(a, b, d) < 0
        and orientation(c, d, a) * orientation(c, d, b) < 0
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}

    buffer_pads = {}
    for reference in BUFFER_REFS:
        for pad in footprints[reference].Pads():
            net = pad.GetNetname()
            if net.startswith("BUFY"):
                buffer_pads[net] = point_mm(pad.GetPosition())

    connector_pads = {}
    for reference in CONNECTOR_REFS:
        for pad in footprints[reference].Pads():
            net = pad.GetNetname()
            if net.startswith("MOTION"):
                connector_pads[net] = {
                    "reference": reference,
                    "pin": pad.GetNumber(),
                    "point": point_mm(pad.GetPosition()),
                }

    chains = []
    problems = []
    for reference in RN_REFS:
        pads = {
            pad.GetNumber(): pad for pad in footprints[reference].Pads()
        }
        for pin_a, pin_b in PIN_PAIRS:
            pad_a = pads[str(pin_a)]
            pad_b = pads[str(pin_b)]
            net_a = pad_a.GetNetname()
            net_b = pad_b.GetNetname()
            buffer_net = net_a if net_a.startswith("BUFY") else net_b
            motion_net = net_b if net_a.startswith("BUFY") else net_a
            if buffer_net == "BUFY0" and motion_net == "AUX_GATE":
                continue
            if not buffer_net.startswith("BUFY"):
                if net_a or net_b:
                    problems.append(
                        f"{reference} pins {pin_a}/{pin_b} have no BUFY side"
                    )
                continue
            if not motion_net.startswith("MOTION"):
                problems.append(
                    f"{reference} pins {pin_a}/{pin_b} have no MOTION side"
                )
                continue
            buffer_pad = pad_a if net_a == buffer_net else pad_b
            motion_pad = pad_a if net_a == motion_net else pad_b
            if buffer_net not in buffer_pads:
                problems.append(f"Missing buffer source pad for {buffer_net}")
                continue
            if motion_net not in connector_pads:
                problems.append(f"Missing connector pad for {motion_net}")
                continue
            target = connector_pads[motion_net]
            chains.append(
                {
                    "buffer_net": buffer_net,
                    "motion_net": motion_net,
                    "rn_reference": reference,
                    "rn_pins": f"{pin_a}/{pin_b}",
                    "buffer_point": buffer_pads[buffer_net],
                    "rn_buffer_point": point_mm(buffer_pad.GetPosition()),
                    "rn_motion_point": point_mm(motion_pad.GetPosition()),
                    "connector_reference": target["reference"],
                    "connector_pin": target["pin"],
                    "connector_point": target["point"],
                }
            )

    active_buffer_nets = {chain["buffer_net"] for chain in chains}
    expected_buffer_nets = {f"BUFY{bit}" for bit in range(1, 16)}
    missing = sorted(expected_buffer_nets - active_buffer_nets)
    extra = sorted(active_buffer_nets - expected_buffer_nets)
    if missing:
        problems.append(f"Missing motion chains: {', '.join(missing)}")
    if extra:
        problems.append(f"Unexpected motion chains: {', '.join(extra)}")

    segments = []
    for chain in chains:
        segments.append(
            (chain["buffer_point"], chain["rn_buffer_point"])
        )
        segments.append(
            (chain["rn_motion_point"], chain["connector_point"])
        )
    crossings = sum(
        crosses(*segments[i], *segments[j])
        for i in range(len(segments))
        for j in range(i + 1, len(segments))
    )

    buffer_order = sorted(chains, key=lambda chain: chain["buffer_point"][0])
    rn_buffer_order = sorted(
        chains, key=lambda chain: chain["rn_buffer_point"][0]
    )
    rn_motion_order = sorted(
        chains, key=lambda chain: chain["rn_motion_point"][0]
    )
    connector_order = sorted(
        chains, key=lambda chain: chain["connector_point"][0]
    )
    if buffer_order != rn_buffer_order:
        problems.append("U24/U25 to RN upper-row order is not monotonic")
    if rn_motion_order != connector_order:
        problems.append("RN lower-row to connector-pin order is not monotonic")
    if crossings:
        problems.append(f"Linear motion fanout has {crossings} crossings")

    total_length = sum(
        math.dist(start, end) for start, end in segments
    )
    physical_order = [
        {
            "position": index + 1,
            "buffer": chain["buffer_net"],
            "motion": chain["motion_net"],
            "rn": f"{chain['rn_reference']}.{chain['rn_pins']}",
            "connector": (
                f"{chain['connector_reference']}."
                f"{chain['connector_pin']}"
            ),
            "x_mm": round(chain["connector_point"][0], 3),
        }
        for index, chain in enumerate(connector_order)
    ]
    report = {
        "active_chains": len(chains),
        "crossings": crossings,
        "total_segment_length_mm": round(total_length, 3),
        "problems": problems,
        "physical_order_left_to_right": physical_order,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
