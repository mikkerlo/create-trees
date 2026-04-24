# create-trees

Optimal **2×2 tree** layouts for a [Create mod](https://www.curseforge.com/minecraft/mc-mods/create) rotating-bearing tree farm.

Live: <https://create-trees.mikkerlo.dev/>

For each chassis count `N` from 3 to 17 (cutting radius `R = N − 1`) the project computes:

- the Euclidean disc of integer tiles `x² + y² ≤ R²` reachable by saws on the bearing,
- every valid 2×2 tree placement (4 tiles inside the disc, none equal to the bearing at `(0, 0)`),
- the **maximum non-overlapping packing** with a 1-block clearance between trees (king-move distance ≥ 3 between anchors),

and renders the result as a static HTML viewer.

A second "structured 3-grid" strategy is included for comparison: trees on a 3×3 lattice offset so the bearing's row and column stay clear.

## Repository layout

| File | Purpose |
| --- | --- |
| `solve.py` | CP-SAT (OR-tools) solver for the maximum independent set; multi-core. |
| `greedy.py` | Structured 3-grid placement and ordering helpers. |
| `build_html.py` | Runs both solvers and emits `index.html` with all 15 layouts embedded as JSON. |
| `plot.py`, `plot_ratio.py` | Matplotlib charts for trees-vs-chassis and trees-per-chassis. |
| `index.html` | Self-contained viewer (deployed by GitHub Pages). |
| `CNAME` | Custom domain for Pages. |

## Replicate the results locally

Requires Python 3.10+.

```bash
git clone https://github.com/mikkerlo/create-trees.git
cd create-trees
pip install ortools matplotlib
python3 solve.py            # prints summary table + per-radius grids
python3 build_html.py       # regenerates index.html
python3 plot.py             # writes trees_vs_chassis.png
python3 plot_ratio.py       # writes trees_per_chassis.png
```

`solve.py` runs CP-SAT with `num_search_workers = os.cpu_count()`. On a 32-core machine all 15 sizes solve in about 1 s wall time and CP-SAT proves optimality.

Open `index.html` in a browser to use the viewer offline.

## Algorithm notes

Two anchors `(x₁, y₁)`, `(x₂, y₂)` conflict iff `|x₁ − x₂| ≤ 2` and `|y₁ − y₂| ≤ 2`. The problem is a maximum independent set on this conflict graph, modelled as a 0/1 ILP:

```
maximize Σ xᵢ
subject to xᵢ + xⱼ ≤ 1     for every conflicting pair (i, j)
           xᵢ ∈ {0, 1}
```

CP-SAT solves it exactly. For the largest case (N = 17, ≈ 730 candidate anchors, ≈ 8 400 conflict edges) it returns and proves optimality in well under a second.

## Results summary

| Chassis | Radius | Max 2×2 trees |
|:---:|:---:|:---:|
| 3 | 2 | 0 |
| 4 | 3 | 4 |
| 5 | 4 | 4 |
| 6 | 5 | 8 |
| 7 | 6 | 12 |
| 8 | 7 | 14 |
| 9 | 8 | 20 |
| 10 | 9 | 28 |
| 11 | 10 | 33 |
| 12 | 11 | 40 |
| 13 | 12 | 50 |
| 14 | 13 | 56 |
| 15 | 14 | 66 |
| 16 | 15 | 78 |
| 17 | 16 | 86 |

Saplings per layout = `4 × trees` (one per footprint tile). N = 5 is the only "wasted" chassis — it adds no trees over N = 4.

## Deploying your own copy on GitHub Pages with a custom subdomain

Replace `create-trees.mikkerlo.dev` with your domain.

1. **DNS** at your domain registrar — add a CNAME record:
   ```
   create-trees   CNAME   <username>.github.io.
   ```
2. **Repo** — fork or push this directory; make sure the `CNAME` file at the repo root contains your domain.
3. **Enable Pages** (root of `main`):
   ```bash
   gh api -X POST repos/<username>/<repo>/pages \
     -f 'source[branch]=main' -f 'source[path]=/'
   ```
4. **Wait** for Let's Encrypt to verify the domain (usually 5–15 min):
   ```bash
   gh api repos/<username>/<repo>/pages | jq '.status, .https_certificate.state'
   ```
5. **Enforce HTTPS** once the certificate state is `approved`:
   ```bash
   gh api -X PUT repos/<username>/<repo>/pages -F https_enforced=true
   ```

The viewer is a single self-contained HTML file (≈ 20 KB with all 15 layouts inlined as JSON), so any static host works — Netlify, Cloudflare Pages, S3, `python -m http.server`, etc.
