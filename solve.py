#!/usr/bin/env python3
"""Brute-force 2x2 tree packing on Create mod rotating tree farm.

For each chassis count N from 3..17 (radius R = N-1), find the maximum
number of 2x2 tree footprints that fit inside the Euclidean disc of
radius R, excluding the bearing tile (0,0), with a 1-block clearance
(in king-move distance) between any two trees.

Two anchors (x1,y1), (x2,y2) conflict iff |dx|<=2 AND |dy|<=2.

Uses OR-tools CP-SAT solver (multi-core, exact).
"""
import os
import string
from ortools.sat.python import cp_model


def find_anchors(R):
    """Return list of (x,y) anchors whose 2x2 footprint fits in disc."""
    R2 = R * R
    anchors = []
    for x in range(-R - 1, R + 2):
        for y in range(-R - 1, R + 2):
            tiles = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
            if all(tx * tx + ty * ty <= R2 and (tx, ty) != (0, 0)
                   for tx, ty in tiles):
                anchors.append((x, y))
    return anchors


def solve_mis_cpsat(anchors, num_workers=None):
    """Solve maximum independent set using CP-SAT, returns chosen anchors."""
    n = len(anchors)
    if n == 0:
        return [], True

    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"a_{i}") for i in range(n)]

    # Bucket anchors by cell for O(n) neighbor lookup
    pos_to_idx = {a: i for i, a in enumerate(anchors)}

    seen_pairs = set()
    for i, (x1, y1) in enumerate(anchors):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                j = pos_to_idx.get((x1 + dx, y1 + dy))
                if j is None or j <= i:
                    continue
                seen_pairs.add((i, j))

    for (i, j) in seen_pairs:
        model.Add(xs[i] + xs[j] <= 1)

    model.Maximize(sum(xs))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = num_workers or os.cpu_count() or 8
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), \
        f"Solver returned {solver.StatusName(status)}"
    optimal = (status == cp_model.OPTIMAL)

    chosen = [anchors[i] for i in range(n) if solver.Value(xs[i]) == 1]
    return chosen, optimal


def render_grid(R, trees):
    """Render the disc grid with trees labeled A,B,C,..."""
    R2 = R * R
    # Stable labeling: top-to-bottom, left-to-right.
    # Greedy palette: pick a character that doesn't collide with any
    # already-labeled tree within king-distance 2 (i.e. any tree whose
    # exclusion zone touches this one). With clearance >=1 between
    # trees, only a handful of neighbors can collide, so a small
    # palette suffices for any radius.
    trees_sorted = sorted(trees, key=lambda t: (-t[1], t[0]))
    palette = (string.ascii_uppercase + string.ascii_lowercase
               + string.digits + "@$%&+=?<>~")
    cell_label = {}
    chosen = {}  # anchor -> char
    for (ax, ay) in trees_sorted:
        forbidden = set()
        for (bx, by), ch in chosen.items():
            if abs(ax - bx) <= 4 and abs(ay - by) <= 4:
                forbidden.add(ch)
        ch = next((c for c in palette if c not in forbidden), "#")
        chosen[(ax, ay)] = ch
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            cell_label[(ax + dx, ay + dy)] = ch

    xmin, xmax = -R, R
    ymin, ymax = -R, R

    lines = []
    header = "    " + " ".join(f"{x:2d}" for x in range(xmin, xmax + 1))
    lines.append(header)
    for y in range(ymax, ymin - 1, -1):
        cells = []
        for x in range(xmin, xmax + 1):
            if (x, y) == (0, 0):
                cells.append(" *")
            elif (x, y) in cell_label:
                cells.append(f" {cell_label[(x, y)]}")
            elif x * x + y * y <= R2:
                cells.append(" .")
            else:
                cells.append("  ")
        lines.append(f"{y:3d} " + " ".join(cells))
    return "\n".join(lines)


def main():
    results = []  # (N, R, count, trees, optimal)
    for N in range(3, 18):
        R = N - 1
        anchors = find_anchors(R)
        trees, optimal = solve_mis_cpsat(anchors)
        results.append((N, R, len(trees), trees, optimal))
        tag = "" if optimal else " (not proven optimal)"
        print(f"  solved N={N:2d} R={R:2d}: {len(trees):3d} trees "
              f"({len(anchors)} anchors){tag}", flush=True)

    print()
    # Validation
    for N, R, count, _, _ in results:
        if N == 4:
            assert count == 4, f"VALIDATION FAILED: N=4 expected 4 trees, got {count}"
            print("Validation passed: N=4 yields 4 trees.")
            break
    print()

    # Summary table
    print("Chassis | Radius | Max 2x2 Trees")
    print("--------|--------|---------------")
    for N, R, count, _, opt in results:
        flag = "" if opt else " *"
        print(f"  {N:2d}    |  {R:2d}    |     {count:3d}{flag}")
    print()

    # Meaningful chassis counts
    meaningful = []
    prev_max = -1
    for entry in results:
        if entry[2] > prev_max:
            meaningful.append(entry)
            prev_max = entry[2]

    print("Meaningful chassis counts (where tree count increases):")
    for N, R, count, _, _ in meaningful:
        print(f"- {N} chassis (radius {R}): {count} trees  "
              f"<- first time we reach {count} trees")
    print()

    for N, R, count, trees, _ in meaningful:
        print(f"Radius {R} ({N} chassis): {count} trees")
        print(render_grid(R, trees))
        print()


if __name__ == "__main__":
    main()
