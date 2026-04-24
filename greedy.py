#!/usr/bin/env python3
"""Greedy tree placements for comparison with optimal."""
from solve import find_anchors


def structured_grid(R):
    """3-grid offset so bearing's row and column stay empty.
    Anchors at (3i+1, 3j+1): trees occupy x in {-2,-1},{1,2},{4,5},...
    leaving column 0 (and row 0) clear of footprints.
    Order: ring-by-ring from the bearing, bottom-then-top, left-then-right.
    """
    R2 = R * R
    placed = []
    span = (R // 3) + 2
    for i in range(-span, span + 1):
        for j in range(-span, span + 1):
            x, y = 3 * i + 1, 3 * j + 1
            tiles = ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1))
            if all(tx * tx + ty * ty <= R2 and (tx, ty) != (0, 0)
                   for tx, ty in tiles):
                placed.append((x, y))
    # Order: by Chebyshev ring (max abs of anchor center), then below
    # before above, then left before right -- so tree #1 ends up
    # bottom-left of the inner ring, #2 bottom-right, #3 top-left, etc.
    def key(a):
        cx, cy = a[0] + 0.5, a[1] + 0.5
        ring = max(abs(cx), abs(cy))
        return (ring, cy, cx)  # cy ascending = below first
    placed.sort(key=key)
    return placed


def greedy_place(anchors):
    """Sort anchors by distance from origin (anchor center), place greedily."""
    # Anchor center is (x+0.5, y+0.5); distance^2 from origin.
    def key(a):
        x, y = a
        cx, cy = x + 0.5, y + 0.5
        # Tie-break by quadrant for deterministic, symmetric output.
        return (cx * cx + cy * cy, x, y)

    ordered = sorted(anchors, key=key)
    placed = []
    for (x, y) in ordered:
        ok = True
        for (px, py) in placed:
            if abs(x - px) <= 2 and abs(y - py) <= 2:
                ok = False
                break
        if ok:
            placed.append((x, y))
    return placed


if __name__ == "__main__":
    print(f"{'N':>3} {'R':>3} {'struct':>7} {'greedy':>7} {'optimal':>8}")
    optimal_counts = {3:0, 4:4, 5:4, 6:8, 7:12, 8:14, 9:20, 10:28, 11:33,
                      12:40, 13:50, 14:56, 15:66, 16:78, 17:86}
    for N in range(3, 18):
        R = N - 1
        anchors = find_anchors(R)
        g = greedy_place(anchors)
        s = structured_grid(R)
        opt = optimal_counts[N]
        print(f"{N:3d} {R:3d} {len(s):7d} {len(g):7d} {opt:8d}")
