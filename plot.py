#!/usr/bin/env python3
"""Plot trees-per-chassis curve from solver results."""
import matplotlib.pyplot as plt

chassis = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
trees   = [0, 4, 4, 8, 12, 14, 20, 28, 33, 40, 50, 56, 66, 78, 86]

# Identify "wasted" chassis (no improvement over previous)
wasted = []
prev = -1
for n, t in zip(chassis, trees):
    if t == prev:
        wasted.append((n, t))
    prev = t

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Left: absolute trees vs chassis
ax1.plot(chassis, trees, marker="o", linewidth=2, color="#2e7d32",
         label="Max 2x2 trees (CP-SAT optimal)")
for n, t in wasted:
    ax1.plot(n, t, marker="X", markersize=14, color="#c62828",
             linestyle="None", label="No gain over previous"
             if n == wasted[0][0] else None)
for n, t in zip(chassis, trees):
    ax1.annotate(str(t), (n, t), textcoords="offset points",
                 xytext=(0, 8), ha="center", fontsize=9)
ax1.set_xlabel("Chassis count (N)")
ax1.set_ylabel("Maximum 2x2 trees")
ax1.set_title("Max 2x2 trees vs chassis count")
ax1.set_xticks(chassis)
ax1.grid(True, alpha=0.3)
ax1.legend(loc="upper left")

# Right: marginal trees gained per added chassis
deltas = [trees[i] - trees[i - 1] for i in range(1, len(trees))]
delta_n = chassis[1:]
bars = ax2.bar(delta_n, deltas, color=["#c62828" if d == 0 else "#1565c0"
                                       for d in deltas])
for n, d in zip(delta_n, deltas):
    ax2.annotate(f"+{d}", (n, d), textcoords="offset points",
                 xytext=(0, 3), ha="center", fontsize=9)
ax2.set_xlabel("Chassis count (N)")
ax2.set_ylabel("Trees gained over N-1 chassis")
ax2.set_title("Marginal benefit of each added chassis")
ax2.set_xticks(delta_n)
ax2.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
out = "/home/mikkerlo/projects/trees/trees_vs_chassis.png"
plt.savefig(out, dpi=130)
print(f"saved {out}")
