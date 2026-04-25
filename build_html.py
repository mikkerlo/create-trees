#!/usr/bin/env python3
"""Build a static HTML viewer with embedded layouts for each (target N, saws K).

For every chassis target N (=> radius R = N-1) and saws-placed count K
in 0..R, we precompute the optimal MIS layout in the cutting annulus
(R-K)^2 < d^2 <= R^2, plus the structured-3-grid baseline restricted
to the same annulus. The HTML viewer lets the user slide K and pick R
independently.
"""
import json
from solve import solve_mis_cpsat


def find_anchors_annulus(R, Ru):
    """Anchors whose 2x2 footprint sits entirely in the cutting annulus
    Ru^2 < d^2 <= R^2 and avoids the bearing tile (0,0)."""
    R2 = R * R
    Ru2 = Ru * Ru
    anchors = []
    for x in range(-R - 1, R + 2):
        for y in range(-R - 1, R + 2):
            ok = True
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                tx, ty = x + dx, y + dy
                d2 = tx * tx + ty * ty
                if d2 > R2 or d2 <= Ru2 or (tx, ty) == (0, 0):
                    ok = False
                    break
            if ok:
                anchors.append((x, y))
    return anchors


def structured_annulus(R, Ru):
    """3-grid trees (anchors at (3i+1, 3j+1)) restricted to the annulus."""
    R2 = R * R
    Ru2 = Ru * Ru
    placed = []
    span = (R // 3) + 2
    for i in range(-span, span + 1):
        for j in range(-span, span + 1):
            x, y = 3 * i + 1, 3 * j + 1
            ok = True
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                tx, ty = x + dx, y + dy
                d2 = tx * tx + ty * ty
                if d2 > R2 or d2 <= Ru2 or (tx, ty) == (0, 0):
                    ok = False
                    break
            if ok:
                placed.append((x, y))

    def key(a):
        cx, cy = a[0] + 0.5, a[1] + 0.5
        ring = max(abs(cx), abs(cy))
        return (ring, cy, cx)

    placed.sort(key=key)
    return placed


solutions = {}
for N in range(3, 18):
    R = N - 1
    by_saws = {}
    for K in range(0, R + 1):
        Ru = R - K
        anchors = find_anchors_annulus(R, Ru)
        if anchors:
            opt_trees, _ = solve_mis_cpsat(anchors)
        else:
            opt_trees = []
        struct_trees = structured_annulus(R, Ru)
        by_saws[K] = {"opt": opt_trees, "struct": struct_trees}
        print(f"N={N:2d} K={K:2d} Ru={Ru:2d}: "
              f"opt={len(opt_trees):3d}  struct={len(struct_trees):3d}")
    solutions[N] = {"radius": R, "saws": by_saws}

data_json = json.dumps(solutions, separators=(",", ":"))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Create Mod 2x2 Tree Farm Layout</title>
<style>
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #1a1a1a;
    color: #e0e0e0;
    margin: 0;
    padding: 20px;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ margin-top: 0; color: #81c784; }}
  .controls {{
    display: flex; gap: 20px; align-items: center;
    background: #2a2a2a; padding: 15px; border-radius: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }}
  label {{ font-weight: 600; }}
  select {{
    background: #1a1a1a; color: #e0e0e0;
    border: 1px solid #555; padding: 6px 10px; border-radius: 4px;
    font-size: 16px;
  }}
  .stats {{
    display: flex; gap: 24px; margin-left: auto;
    font-size: 18px;
  }}
  .stat .label {{ color: #888; font-size: 13px; display: block; }}
  .stat .value {{ font-size: 22px; font-weight: 700; color: #81c784; }}
  canvas {{
    background: #2a2a2a; border-radius: 8px;
    display: block; margin: 0 auto;
  }}
  .legend {{
    margin-top: 14px; display: flex; gap: 20px; justify-content: center;
    font-size: 14px;
    flex-wrap: wrap;
  }}
  .swatch {{
    display: inline-block; width: 14px; height: 14px;
    vertical-align: middle; margin-right: 6px; border-radius: 2px;
  }}
  footer {{ margin-top: 24px; text-align: center; color: #777; font-size: 13px; }}
</style>
</head>
<body>
<div class="container">
  <h1>Create Mod &ndash; 2x2 Tree Farm Layout (rotating bearing)</h1>
  <div class="controls">
    <label for="total">Total saws planned (T):</label>
    <input type="range" id="total" min="0" max="16" value="16" step="1" style="flex:1; min-width:280px; max-width:480px">
    <span id="total-label" style="font-weight:700; color:#ffb300; min-width:90px">16 / 16</span>
  </div>
  <div class="controls">
    <label for="chassis">Target chassis (radius):</label>
    <select id="chassis"></select>
    <label style="margin-left:10px">Strategy:</label>
    <label><input type="radio" name="strat" value="optimal" checked> Optimal</label>
    <label><input type="radio" name="strat" value="structured"> Structured 3-grid</label>
    <div class="stats">
      <div class="stat"><span class="label">Radius</span><span class="value" id="stat-radius">-</span></div>
      <div class="stat"><span class="label">Trees (cuttable/planned)</span><span class="value" id="stat-trees">-</span></div>
      <div class="stat"><span class="label">Saplings (cuttable/planned)</span><span class="value" id="stat-saplings">-</span></div>
      <div class="stat"><span class="label">Yield (blocks/h)</span><span class="value" id="stat-yield">-</span></div>
      <div class="stat"><span class="label">vs optimal at T</span><span class="value" id="stat-gap">-</span></div>
    </div>
  </div>
  <div class="controls">
    <label for="current">Saws placed (K of T):</label>
    <input type="range" id="current" min="0" max="16" value="16" step="1" style="flex:1; min-width:280px; max-width:480px">
    <span id="current-label" style="font-weight:700; color:#81c784; min-width:90px">16 / 16</span>
    <label style="margin-left:10px">Blocks/tree/hour:</label>
    <input type="number" id="rate" min="0" step="1" value="713" style="width:90px; background:#1a1a1a; color:#e0e0e0; border:1px solid #555; padding:4px 8px; border-radius:4px;">
    <span style="color:#888; font-size:13px">(default 712.75 = your 17106/24 measurement at 4 RPM)</span>
  </div>
  <canvas id="grid" width="900" height="900"></canvas>
  <div class="legend">
    <span><span class="swatch" style="background:#388e3c"></span>Cuttable tree (entire footprint in current cutting ring)</span>
    <span><span class="swatch" style="background:#1b3a1c;border:1px dashed #4a704c"></span>Planned tree (not yet cuttable at K)</span>
    <span><span class="swatch" style="background:#4a3a26"></span>Cutting ring (current saws)</span>
    <span><span class="swatch" style="background:#3a3a3a"></span>Planned future ring (saws not yet placed)</span>
    <span><span class="swatch" style="background:#262626"></span>Off-plan (never planned to cut)</span>
    <span><span class="swatch" style="background:#ffb300"></span>Mechanical bearing</span>
  </div>
  <footer>Layout is precomputed for each (target chassis, total saws T)
   pair: optimal MIS via CP-SAT, restricted so every 2x2 footprint
   lies in the planned cutting ring (R-T)<sup>2</sup> &lt;
   x<sup>2</sup>+y<sup>2</sup> &le; R<sup>2</sup>. The "Saws placed K"
   slider then dims trees still inside the inner uncovered region
   d<sup>2</sup> &le; (R-K)<sup>2</sup>. Saplings = 4 x trees.</footer>
</div>
<script>
const SOLUTIONS = {data_json};
const SAPLINGS_PER_TREE = 4;
const canvas = document.getElementById('grid');
const ctx = canvas.getContext('2d');
const select = document.getElementById('chassis');
const totalSlider = document.getElementById('total');
const totalLabel = document.getElementById('total-label');
const currentSlider = document.getElementById('current');
const currentLabel = document.getElementById('current-label');
const rateInput = document.getElementById('rate');

Object.keys(SOLUTIONS).map(Number).sort((a,b) => a-b).forEach(n => {{
  const opt = document.createElement('option');
  opt.value = n;
  opt.textContent = `${{n}} chassis`;
  select.appendChild(opt);
}});

function currentStrategy() {{
  return document.querySelector('input[name="strat"]:checked').value;
}}

function refreshDropdown(T) {{
  for (let i = 0; i < select.options.length; i++) {{
    const opt = select.options[i];
    const n = Number(opt.value);
    const sol = SOLUTIONS[n];
    const Teff = Math.min(T, sol.radius);
    const o = sol.saws[Teff];
    opt.textContent = `${{n}} chassis (R=${{sol.radius}}, T=${{Teff}}: opt ${{o.opt.length}} / struct ${{o.struct.length}})`;
  }}
}}

function isTreeCuttable(ax, ay, Ru2) {{
  for (const [dx, dy] of [[0,0],[1,0],[0,1],[1,1]]) {{
    const tx = ax + dx, ty = ay + dy;
    if (tx * tx + ty * ty <= Ru2) return false;
  }}
  return true;
}}

function render() {{
  const N = Number(select.value);
  const sol = SOLUTIONS[N];
  const R = sol.radius;

  // Total saws T: cap to current target's R, used to pick the layout.
  totalSlider.max = R;
  let T = Number(totalSlider.value);
  if (T > R) {{ T = R; totalSlider.value = R; }}
  if (T < 0) {{ T = 0; totalSlider.value = 0; }}
  totalLabel.textContent = `${{T}} / ${{R}}`;

  // Saws placed K: 0..T (can't place more than planned).
  currentSlider.max = T;
  let K = Number(currentSlider.value);
  if (K > T) {{ K = T; currentSlider.value = T; }}
  if (K < 0) {{ K = 0; currentSlider.value = 0; }}
  currentLabel.textContent = `${{K}} / ${{T}}`;

  // Planned outer ring (warm zone in stats / disc): (R-T)^2 < d^2 <= R^2
  // Currently cuttable ring: (R-K)^2 < d^2 <= R^2
  const Rt = R - T;
  const Rt2 = Rt * Rt;
  const Rc = R - K;
  const Rc2 = Rc * Rc;

  refreshDropdown(T);

  const strat = currentStrategy();
  const sawsData = sol.saws[T];
  const trees = (strat === 'optimal') ? sawsData.opt : sawsData.struct;
  const optCount = sawsData.opt.length;
  const treeCount = trees.length;
  const cuttable = trees.filter(([ax, ay]) => isTreeCuttable(ax, ay, Rc2));
  const cuttableCount = cuttable.length;
  const saplings = treeCount * SAPLINGS_PER_TREE;
  const cuttableSaplings = cuttableCount * SAPLINGS_PER_TREE;
  const gap = treeCount - optCount;

  const rate = Math.max(0, Number(rateInput.value) || 0);
  const yieldNow = cuttableCount * rate;
  const yieldFull = treeCount * rate;
  function fmt(n) {{
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M';
    if (n >= 10_000) return (n / 1_000).toFixed(1) + 'k';
    if (n >= 1_000) return n.toLocaleString();
    return Math.round(n).toString();
  }}

  document.getElementById('stat-radius').textContent = `${{R}}`;
  document.getElementById('stat-trees').textContent = `${{cuttableCount}} / ${{treeCount}}`;
  document.getElementById('stat-saplings').textContent = `${{cuttableSaplings}} / ${{saplings}}`;
  document.getElementById('stat-yield').textContent = `${{fmt(yieldNow)}} / ${{fmt(yieldFull)}}`;
  const gapEl = document.getElementById('stat-gap');
  if (strat === 'optimal') {{
    gapEl.textContent = '0';
    gapEl.style.color = '#81c784';
  }} else {{
    gapEl.textContent = (gap >= 0 ? '+' : '') + gap;
    gapEl.style.color = gap < 0 ? '#ef5350' : '#81c784';
  }}

  // Grid spans tiles from -R to R inclusive.
  const tilesPerSide = 2 * R + 1;
  const cell = Math.floor(Math.min(canvas.width, canvas.height) / (tilesPerSide + 2));
  const gridPx = cell * tilesPerSide;
  const offsetX = Math.floor((canvas.width - gridPx) / 2);
  const offsetY = Math.floor((canvas.height - gridPx) / 2);

  function tileToPx(tx, ty) {{
    const col = tx + R;
    const row = R - ty;
    return [offsetX + col * cell, offsetY + row * cell];
  }}

  ctx.fillStyle = '#1a1a1a';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#222';
  ctx.fillRect(offsetX, offsetY, gridPx, gridPx);

  // Disc tiles: three shades.
  //   warm  (#4a3a26) = currently cutting (saws placed):    Rc^2 < d^2 <= R^2
  //   cool  (#3a3a3a) = planned future ring (no saw yet):   Rt^2 < d^2 <= Rc^2
  //   dim   (#262626) = off-plan inside disc:               d^2 <= Rt^2
  const R2 = R * R;
  for (let tx = -R; tx <= R; tx++) {{
    for (let ty = -R; ty <= R; ty++) {{
      const d2 = tx * tx + ty * ty;
      if (d2 <= R2) {{
        const [px, py] = tileToPx(tx, ty);
        let color;
        if (d2 > Rc2) color = '#4a3a26';
        else if (d2 > Rt2) color = '#3a3a3a';
        else color = '#262626';
        ctx.fillStyle = color;
        ctx.fillRect(px + 1, py + 1, cell - 2, cell - 2);
      }}
    }}
  }}

  // Tree footprints. Every tree in this layout is "planned" (fits inside
  // the planned cutting ring). Highlight only those whose entire 2x2
  // also fits inside the currently-cuttable ring.
  trees.forEach(([ax, ay], idx) => {{
    const active = isTreeCuttable(ax, ay, Rc2);
    const fillColor = active ? '#388e3c' : '#1b3a1c';
    const strokeColor = active ? '#81c784' : '#4a704c';
    const labelColor = active ? '#ffffff' : '#7aa17c';
    for (const [dx, dy] of [[0,0],[1,0],[0,1],[1,1]]) {{
      const [px, py] = tileToPx(ax + dx, ay + dy);
      ctx.fillStyle = fillColor;
      ctx.fillRect(px + 1, py + 1, cell - 2, cell - 2);
    }}
    const [px, py] = tileToPx(ax, ay + 1);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    if (!active) ctx.setLineDash([4, 3]);
    ctx.strokeRect(px + 1, py + 1, cell * 2 - 2, cell * 2 - 2);
    ctx.setLineDash([]);
    if (cell >= 14) {{
      ctx.fillStyle = labelColor;
      ctx.font = `bold ${{Math.max(10, Math.floor(cell * 0.6))}}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(idx + 1), px + cell, py + cell);
    }}
  }});

  // Bearing
  const [bx, by] = tileToPx(0, 0);
  ctx.fillStyle = '#ffb300';
  ctx.fillRect(bx + 1, by + 1, cell - 2, cell - 2);
  ctx.fillStyle = '#1a1a1a';
  ctx.font = `bold ${{Math.max(10, Math.floor(cell * 0.7))}}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('B', bx + cell / 2, by + cell / 2);

  // Axis ticks every 5 tiles
  ctx.fillStyle = '#888';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let tx = -R; tx <= R; tx++) {{
    if (tx % 5 === 0) {{
      const [px] = tileToPx(tx, 0);
      ctx.fillText(String(tx), px + cell / 2, offsetY + gridPx + 4);
    }}
  }}
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let ty = -R; ty <= R; ty++) {{
    if (ty % 5 === 0) {{
      const [, py] = tileToPx(0, ty);
      ctx.fillText(String(ty), offsetX - 4, py + cell / 2);
    }}
  }}
}}

const STORAGE_KEY = 'create-tree-farm-prefs-v5';
function savePrefs() {{
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify({{
      target: select.value,
      total: totalSlider.value,
      placed: currentSlider.value,
      strategy: currentStrategy(),
      rate: rateInput.value,
    }}));
  }} catch (e) {{ /* ignore */ }}
}}
function loadPrefs() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  }} catch (e) {{ return null; }}
}}

function rerender() {{
  render();
  savePrefs();
}}
select.addEventListener('change', rerender);
totalSlider.addEventListener('input', () => {{
  // When total saws shrinks, clamp placed too.
  if (Number(currentSlider.value) > Number(totalSlider.value)) {{
    currentSlider.value = totalSlider.value;
  }}
  rerender();
}});
currentSlider.addEventListener('input', rerender);
rateInput.addEventListener('input', rerender);
document.querySelectorAll('input[name="strat"]').forEach(
    el => el.addEventListener('change', rerender));

const prefs = loadPrefs();
if (prefs && SOLUTIONS[prefs.target]) {{
  select.value = prefs.target;
  const targetR = SOLUTIONS[prefs.target].radius;
  totalSlider.max = targetR;
  let savedT = (prefs.total !== undefined) ? Number(prefs.total) : targetR;
  if (savedT > targetR) savedT = targetR;
  if (savedT < 0) savedT = 0;
  totalSlider.value = savedT;
  currentSlider.max = savedT;
  let savedK = (prefs.placed !== undefined) ? Number(prefs.placed) : savedT;
  if (savedK > savedT) savedK = savedT;
  if (savedK < 0) savedK = 0;
  currentSlider.value = savedK;
  if (prefs.rate !== undefined) rateInput.value = prefs.rate;
  const stratEl = document.querySelector(
      `input[name="strat"][value="${{prefs.strategy}}"]`);
  if (stratEl) stratEl.checked = true;
}} else {{
  select.value = '17';
  const R17 = SOLUTIONS['17'].radius;
  totalSlider.max = R17;
  totalSlider.value = R17;
  currentSlider.max = R17;
  currentSlider.value = R17;
}}
render();
</script>
</body>
</html>
"""

out = "/home/mikkerlo/projects/trees/index.html"
with open(out, "w") as f:
    f.write(html)
print(f"wrote {out} ({len(html) // 1024} KB)")
