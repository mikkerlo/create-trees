#!/usr/bin/env python3
"""Build a static HTML viewer with embedded tree layouts (optimal + greedy)."""
import json
from solve import find_anchors, solve_mis_cpsat
from greedy import structured_grid

solutions = {}
for N in range(3, 18):
    R = N - 1
    anchors = find_anchors(R)
    opt_trees, _ = solve_mis_cpsat(anchors)
    struct_trees = structured_grid(R)
    solutions[N] = {
        "radius": R,
        "optimal": opt_trees,
        "structured": struct_trees,
    }
    print(f"N={N}: optimal={len(opt_trees)} structured={len(struct_trees)}")

data_json = json.dumps(solutions)

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
  <h1>Create Mod – 2x2 Tree Farm Layout (rotating bearing)</h1>
  <div class="controls">
    <label for="chassis">Target chassis:</label>
    <select id="chassis"></select>
    <label style="margin-left:10px">Strategy:</label>
    <label><input type="radio" name="strat" value="optimal" checked> Optimal</label>
    <label><input type="radio" name="strat" value="structured"> Structured 3-grid</label>
  </div>
  <div class="controls">
    <label for="current">Saws placed (outside-in):</label>
    <input type="range" id="current" min="0" max="16" value="16" step="1" style="flex:1; max-width:400px">
    <span id="current-label" style="font-weight:700; color:#81c784; min-width:90px">16 / 16</span>
    <div class="stats">
      <div class="stat"><span class="label">Radius</span><span class="value" id="stat-radius">-</span></div>
      <div class="stat"><span class="label">Trees (cuttable/total)</span><span class="value" id="stat-trees">-</span></div>
      <div class="stat"><span class="label">Saplings (cuttable/total)</span><span class="value" id="stat-saplings">-</span></div>
      <div class="stat"><span class="label">vs optimal</span><span class="value" id="stat-gap">-</span></div>
    </div>
  </div>
  <canvas id="grid" width="900" height="900"></canvas>
  <div class="legend">
    <span><span class="swatch" style="background:#388e3c"></span>Cuttable tree (entire footprint in the warm outer annulus)</span>
    <span><span class="swatch" style="background:#1b3a1c;border:1px dashed #4a704c"></span>Not yet cuttable (some tile still in inner uncovered zone)</span>
    <span><span class="swatch" style="background:#4a3a26"></span>Cutting annulus (saws placed)</span>
    <span><span class="swatch" style="background:#3a3a3a"></span>Inner uncovered (no saw yet)</span>
    <span><span class="swatch" style="background:#ffb300"></span>Mechanical bearing</span>
  </div>
  <footer>Layouts proven optimal by OR-tools CP-SAT. Saplings = 4 x trees (one per footprint tile).</footer>
</div>
<script>
const SOLUTIONS = {data_json};
const SAPLINGS_PER_TREE = 4;
const canvas = document.getElementById('grid');
const ctx = canvas.getContext('2d');
const select = document.getElementById('chassis');

Object.keys(SOLUTIONS).map(Number).sort((a,b) => a-b).forEach(n => {{
  const opt = document.createElement('option');
  opt.value = n;
  const s = SOLUTIONS[n];
  opt.textContent = `${{n}} chassis (radius ${{s.radius}}, opt ${{s.optimal.length}} / struct ${{s.structured.length}})`;
  select.appendChild(opt);
}});

function currentStrategy() {{
  return document.querySelector('input[name="strat"]:checked').value;
}}

const currentSlider = document.getElementById('current');
const currentLabel = document.getElementById('current-label');

function isTreeCuttable(ax, ay, Ru2) {{
  // Tree is cuttable iff every footprint tile is in the cutting annulus,
  // i.e. strictly outside the inner-uncovered disc of radius Ru.
  for (const [dx, dy] of [[0,0],[1,0],[0,1],[1,1]]) {{
    const tx = ax + dx, ty = ay + dy;
    if (tx * tx + ty * ty <= Ru2) return false;
  }}
  return true;
}}

function render(N) {{
  const sol = SOLUTIONS[N];
  const R = sol.radius;
  const strat = currentStrategy();
  const trees = sol[strat];
  const optCount = sol.optimal.length;
  const treeCount = trees.length;

  // Slider goes 0..R (saws placed, outside-in). Adjust max to current target.
  currentSlider.max = R;
  let K = Number(currentSlider.value);
  if (K > R) {{ K = R; currentSlider.value = R; }}
  if (K < 0) {{ K = 0; currentSlider.value = 0; }}
  const Ru = R - K;            // inner-uncovered radius
  const Ru2 = Ru * Ru;
  currentLabel.textContent = `${{K}} / ${{R}}`;

  const cuttable = trees.filter(([ax, ay]) => isTreeCuttable(ax, ay, Ru2));
  const cuttableCount = cuttable.length;
  const saplings = treeCount * SAPLINGS_PER_TREE;
  const cuttableSaplings = cuttableCount * SAPLINGS_PER_TREE;
  const gap = treeCount - optCount;

  document.getElementById('stat-radius').textContent = `${{R}}`;
  document.getElementById('stat-trees').textContent = `${{cuttableCount}} / ${{treeCount}}`;
  document.getElementById('stat-saplings').textContent = `${{cuttableSaplings}} / ${{saplings}}`;
  const gapEl = document.getElementById('stat-gap');
  if (strat === 'optimal') {{
    gapEl.textContent = '0';
    gapEl.style.color = '#81c784';
  }} else {{
    gapEl.textContent = (gap >= 0 ? '+' : '') + gap;
    gapEl.style.color = gap < 0 ? '#ef5350' : '#81c784';
  }}

  // Grid spans tiles from -R to R inclusive (size 2R+1 tiles).
  const tilesPerSide = 2 * R + 1;
  const cell = Math.floor(Math.min(canvas.width, canvas.height) / (tilesPerSide + 2));
  const gridPx = cell * tilesPerSide;
  const offsetX = Math.floor((canvas.width - gridPx) / 2);
  const offsetY = Math.floor((canvas.height - gridPx) / 2);

  // World tile (tx,ty) -> canvas (x,y) of tile's top-left.
  // Screen y grows downward; world y grows upward => flip.
  function tileToPx(tx, ty) {{
    const col = tx + R;       // 0..2R
    const row = R - ty;       // 0..2R, top is +R
    return [offsetX + col * cell, offsetY + row * cell];
  }}

  ctx.fillStyle = '#1a1a1a';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Out-of-range backdrop
  ctx.fillStyle = '#222';
  ctx.fillRect(offsetX, offsetY, gridPx, gridPx);

  // Disc tiles. Two shades: warm = cutting annulus (saws cover it),
  // cool = inner uncovered (still need saws).
  const R2 = R * R;
  for (let tx = -R; tx <= R; tx++) {{
    for (let ty = -R; ty <= R; ty++) {{
      const d2 = tx * tx + ty * ty;
      if (d2 <= R2) {{
        const [px, py] = tileToPx(tx, ty);
        ctx.fillStyle = (d2 > Ru2) ? '#4a3a26' : '#3a3a3a';
        ctx.fillRect(px + 1, py + 1, cell - 2, cell - 2);
      }}
    }}
  }}

  // Tree footprints
  trees.forEach(([ax, ay], idx) => {{
    const active = isTreeCuttable(ax, ay, Ru2);
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

  // (Inner-cover area is shaded by the disc-tile loop above; no smooth
  // circle here -- the integer-grid criterion would be misleading.)

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
  ctx.strokeStyle = '#555';
  ctx.lineWidth = 1;
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

const STORAGE_KEY = 'create-tree-farm-prefs-v2';
function savePrefs() {{
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify({{
      target: select.value,
      saws: currentSlider.value,
      strategy: currentStrategy(),
    }}));
  }} catch (e) {{ /* private mode etc -- ignore */ }}
}}
function loadPrefs() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  }} catch (e) {{ return null; }}
}}

function rerender() {{
  render(Number(select.value));
  savePrefs();
}}
select.addEventListener('change', () => {{
  // Slider max gets re-clamped inside render() based on the new target's R.
  rerender();
}});
currentSlider.addEventListener('input', rerender);
document.querySelectorAll('input[name="strat"]').forEach(
    el => el.addEventListener('change', rerender));

const prefs = loadPrefs();
if (prefs && SOLUTIONS[prefs.target]) {{
  select.value = prefs.target;
  const targetR = SOLUTIONS[prefs.target].radius;
  currentSlider.max = targetR;
  let savedSaws = (prefs.saws !== undefined) ? Number(prefs.saws) : targetR;
  if (savedSaws > targetR) savedSaws = targetR;
  if (savedSaws < 0) savedSaws = 0;
  currentSlider.value = savedSaws;
  const stratEl = document.querySelector(
      `input[name="strat"][value="${{prefs.strategy}}"]`);
  if (stratEl) stratEl.checked = true;
}} else {{
  select.value = '17';
  currentSlider.max = SOLUTIONS['17'].radius;
  currentSlider.value = SOLUTIONS['17'].radius;
}}
render(Number(select.value));
</script>
</body>
</html>
"""

out = "/home/mikkerlo/projects/trees/index.html"
with open(out, "w") as f:
    f.write(html)
print(f"wrote {out}")
