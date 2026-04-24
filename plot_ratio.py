#!/usr/bin/env python3
"""Plot trees-per-chassis ratio."""
import matplotlib.pyplot as plt

chassis = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
trees   = [0, 4, 4, 8, 12, 14, 20, 28, 33, 40, 50, 56, 66, 78, 86]
ratio = [t / n for t, n in zip(trees, chassis)]

best_idx = max(range(len(chassis)), key=lambda i: ratio[i])

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(chassis, ratio, marker="o", linewidth=2, color="#6a1b9a")
for n, r in zip(chassis, ratio):
    ax.annotate(f"{r:.2f}", (n, r), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=9)
ax.plot(chassis[best_idx], ratio[best_idx], marker="*",
        markersize=20, color="#f9a825",
        label=f"best ratio: N={chassis[best_idx]} ({ratio[best_idx]:.3f})")
ax.set_xlabel("Chassis count (N)")
ax.set_ylabel("Trees per chassis")
ax.set_title("Trees / chassis efficiency")
ax.set_xticks(chassis)
ax.grid(True, alpha=0.3)
ax.legend(loc="lower right")

plt.tight_layout()
out = "/home/mikkerlo/projects/trees/trees_per_chassis.png"
plt.savefig(out, dpi=130)
print(f"saved {out}")
