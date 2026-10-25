"""Place one functional module on the current staged PCB.

Footprints already inside the board are treated as fixed. Parked footprints
belonging to the requested sheet are placed by weighted connectivity, followed
by a bounded local refinement. Components from other sheets remain parked.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--region", help="x1,y1,x2,y2 placement region in mm")
    parser.add_argument(
        "--refs",
        help="Comma-separated component references to place instead of the whole sheet",
    )
    parser.add_argument(
        "--side",
        choices=("front", "back"),
        help="Force selected components to this board side before placement",
    )
    parser.add_argument(
        "--reflow-existing",
        action="store_true",
        help="Reposition all non-connector components from this module",
    )
    parser.add_argument(
        "--power-priority",
        action="store_true",
        help="Increase the placement weight of power nets",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    import generate_pcb
    from generate_pcb import REGIONS, add_to_occupancy, candidate_boxes
    from generate_pcb import choose_connected_spot, component_points, net_weight
    from generate_pcb import occupancy_for, parse_netlist, refine_placement

    if args.power_priority:
        base_weight = generate_pcb.net_weight

        def power_weight(name: str) -> float:
            if name.startswith(("VIN", "BUCK", "MODULE_5V")):
                return 3.0
            if name.startswith(("+5", "+3V3", "USB", "BL_VIN")):
                return 2.0
            if name in {"PGND", "AGND", "GND"}:
                return 0.0
            return base_weight(name)

        generate_pcb.net_weight = power_weight

    components = {component.reference: component for component in parse_netlist()}
    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )

    def is_inside(footprint) -> bool:
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]

    inside_refs = {reference for reference, footprint in footprints.items() if is_inside(footprint)}
    if args.refs:
        requested = {item.strip() for item in args.refs.split(",") if item.strip()}
        unknown = sorted(requested - set(components))
        if unknown:
            raise SystemExit(f"Unknown component references: {unknown}")
        target_refs = requested
    else:
        target_refs = {
            reference
            for reference, component in components.items()
            if component.sheet == args.sheet
            and (args.reflow_existing or reference not in inside_refs)
            and not reference.startswith("J")
        }
    if not target_refs:
        raise SystemExit(f"No parked footprints found for sheet: {args.sheet}")

    if args.side:
        back = args.side == "back"
        for reference in target_refs:
            generate_pcb.put_on_side(footprints[reference], back)

    if args.region:
        region = tuple(float(value) for value in args.region.split(","))
        if len(region) != 4:
            raise SystemExit("--region requires x1,y1,x2,y2")
    else:
        region = REGIONS[args.sheet]

    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    boxes = {}
    net_points = defaultdict(list)
    fixed_inside_refs = inside_refs - target_refs
    for reference in fixed_inside_refs:
        footprint = footprints[reference]
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        rotation = footprint.GetOrientationDegrees()
        box = candidate_boxes(footprint, x, y)
        add_to_occupancy(footprint, box, occupied)
        boxes[reference] = box
        component = components.get(reference)
        if component is None:
            continue
        for net, px, py in component_points(component, footprint, x, y, rotation):
            net_points[net].append((reference, px, py))

    pending = set(target_refs)
    while pending:
        def priority(reference: str):
            component = components[reference]
            active_nets = {net for net in component.nets.values() if net_weight(net) > 0}
            attached = sum(1 for net in active_nets if net_points.get(net))
            return (attached, reference.startswith(("U", "Q", "L")), len(active_nets), len(component.nets))

        reference = max(pending, key=lambda item: (priority(item), item))
        component = components[reference]
        footprint = footprints[reference]
        _, x, y, rotation, box, points = choose_connected_spot(
            component,
            footprint,
            region,
            occupancy_for(footprint, occupied),
            net_points,
        )
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        add_to_occupancy(footprint, box, occupied)
        boxes[reference] = box
        for net, px, py in points:
            net_points[net].append((reference, px, py))
        pending.remove(reference)
        print(f"{reference:6s} -> ({x:7.2f}, {y:7.2f}) rot={rotation:5.1f}")

    fixed_for_refine = set(components) - target_refs
    refined = refine_placement(
        list(components.values()),
        footprints,
        fixed_for_refine,
        boxes,
        net_points,
        lambda component: region,
    )
    print(f"placed module {args.sheet!r}: {len(target_refs)} footprints")
    if args.dry_run:
        return
    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
