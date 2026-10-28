# Media: scenes, charts and (last) animations

Three kinds of answer need more than a paragraph: **what changes, step by step** (scene), **how much, compared to
what** (chart), and **continuous motion** (animation). All three are prepared at authoring time and inlined, so the
reader still gets one self-contained page with no network and no scripts of its own.

```
media/
  scenes/<name>.yaml   a scene: what the picture contains, and what each click changes  ← start here
  <name>.vl.json       a chart: a Vega-Lite spec; CSVs it reads sit next to it
  src/<name>/          an animation: a Motion Canvas project, a Manim scene, or exported stills
  <name>.json          BAKED manifest — commit it
  <name>.webp          BAKED sprite sheet (animation only) — commit it
```

```html
<ex-scene src="atlas-media:clean-pipeline" source="real" origin="tools/pipeline" caption="…"></ex-scene>
<ex-chart src="atlas-media:throughput" source="real" origin="logs/run-2026-10-26.log" caption="…"></ex-chart>
<ex-anim src="atlas-media:physics" source="illustrative" caption="…"></ex-anim>
```

## Choose the form

| The reader asks | Use |
|---|---|
| "what are the steps, and what goes in/out of each" | `<ex-flow>` / `<ex-stage>` — cheapest, searchable text |
| "what changes between these states, and why" | **`<ex-scene>`** — click-through, labelled, live text |
| "how many, how often, how does it compare" | `<ex-chart>` |
| "…and I want to filter or zoom that" | `<ex-chart interactive>` |
| genuinely continuous motion (a trajectory, a wave, a long animation) | `<ex-anim>` |

**Default to a scene.** A card whose explanation is a list of paragraphs is a card that should have been a scene:
the reader clicks through the states, and the prose shrinks to the one sentence the picture cannot say. A video is the
last resort — it cannot be stopped at a step, searched, translated, or read at the reader's text size, and it costs
hundreds of kilobytes.

## A scene (`<ex-scene>`)

A scene is a small YAML file: boxes, chips, labels, bars, arrows, and a list of steps. The kit draws it as SVG, so the
text is real text — themed, searchable, translated when the card language changes.

```yaml
# media/scenes/clean-pipeline.yaml
size: [700, 250]                       # logical canvas; the kit scales it to the card's column

nodes:
  - {id: row, kind: chip, text: A-1001, sub: "品类=(空)", at: [24, 100], size: [140, 40], tone: accent}
  - {id: clean, kind: box, text: clean, sub: "stage 0", at: [196, 88], size: [126, 64]}
  - {id: index, kind: box, text: index, sub: "stage 1", at: [362, 88], size: [126, 64]}

edges:
  - {from: clean, to: index, label: "写回"}

steps:
  - title: "一行进来，品类是空的"
    detail: "路由要先知道品类；空值没法判断属于哪个体系。"
    show: [row]
    focus: [row]
  - title: "clean 从标签补出品类"
    detail: "label 的 @ 前半段就是品类。"
    show: [clean]
    focus: [clean]
    move: {row: [200, 100]}
    sub: {row: "品类=鞋类"}
```

| Key | Meaning |
|---|---|
| `size` | canvas, default `[720, 300]` |
| `nodes[].id` | letters, digits, `_`, `-`; unique |
| `nodes[].kind` | `box`, `chip`, `label`, `dot`, `bar` |
| `nodes[].at` | top-left `[x, y]` inside `size` (`label`: the text's centre) |
| `nodes[].size` | optional; defaults per kind (`box` 128×56, `chip` 56×32, `dot` 14×14, `bar` 180×16) |
| `nodes[].text` / `.sub` | main line (≤160) and small line (≤120) |
| `nodes[].tone` | `default`, `accent`, `own`, `ok`, `warn`, `del`, `muted` |
| `nodes[].value` | `bar` only: fill ratio 0–1 |
| `edges[].from` / `.to` | node ids; the arrow follows them when they move |
| `edges[].label`, `.dashed` | optional |
| `steps[].title` | **required**: what this click explains (≤120) |
| `steps[].detail` | optional second line (≤400) |
| `steps[].show` / `.hide` | nodes that appear / disappear at this step |
| `steps[].focus` | spotlight: everything else dims; `[]` clears it |
| `steps[].move` | `{node: [x, y]}` — position change, animated |
| `steps[].text` / `.sub` | `{node: "…"}` — live text change (the payload) |
| `steps[].value` | `{bar: 0–1}` |
| `steps[].tone` | `{node: tone}` — recolour on click |

Rules the bake enforces, because they are what makes a scene explain rather than decorate:

1. **Two to twelve steps.** One step is a picture; twelve is a lecture.
2. **Every step has a title**, and every step changes something or says something (`show`, `hide`, `focus`, `move`,
   `text`, `sub`, `value`, `tone`, or a `detail`). A click that changes nothing is a wasted click.
3. **A node nobody mentions is scaffolding** and is visible from the start; a node mentioned by `show` is hidden
   until that step.
4. **Put the payload in the picture**, not in the paragraph: the category the row picks up, the id it gets, the
   branch it takes. Text changes per step are the point.

Bake it like any other media:

```bash
atlas-explainer bake path/to/card                 # or: codeatlas card bake path/to/card
atlas-explainer lint path/to/card                 # stale sources, missing captions, bad ids
```

The scene source travels with the card (`media/scenes/<name>.yaml`) because it is small and is the explanation itself.

## A chart (`<ex-chart>`)

Write a normal [Vega-Lite](https://vega.github.io/vega-lite/) spec in `media/<name>.vl.json`:

```json
{
  "data": {"url": "throughput.csv"},
  "mark": "bar",
  "encoding": {
    "x": {"field": "stage", "type": "nominal"},
    "y": {"field": "rows", "type": "quantitative"},
    "tooltip": [{"field": "stage"}, {"field": "rows"}]
  }
}
```

* `data.url` is **inlined at bake time** from a file next to the spec (CSV or JSON). Remote URLs are rejected — a card
  never fetches anything, and a chart of data you did not read is the same failure as a fabricated table.
* If the spec sets no `width`/`height`, the chart is baked at 620×280 and scaled to the card's column.
* The theme comes from the kit's palette; your spec's own `config` overrides it.
* Every chart is baked twice (light and dark) and shows the right one as the reader switches theme.

### Interaction

`interactive` in `bake.yaml` compiles the spec to Vega as well, and the card carries the Vega runtime (~500 KB):

```yaml
chart:
  throughput:
    spec: throughput.vl.json
    interactive: true
```

That buys real Vega-Lite behaviour — hover tooltips, `params` selections, legend toggles, cross-filtering — under the
card's strict CSP: expressions are *interpreted* (`vega-interpreter`), never compiled with `new Function`, so no
`'unsafe-eval'` is needed. Use it when the reader's question is "and what if I look at only these?", not merely to have
tooltips.

## An animation (`<ex-anim>`) — only for continuous motion

Use it when the motion itself is the answer (a trajectory, an easing curve, a physics clip), not to show a sequence of
states: that is a scene, and a scene is smaller, sharper and clickable.

| Attribute | Meaning |
|---|---|
| `src` | `atlas-media:<name>`; the asset baked from `media/src/<name>/` or `bake.yaml` |
| `caption` | **required** — the reader's text when the picture fails, and the frame's fallback label |
| `source`, `origin`, `at` | same rule as `ex-table`: `real` needs where it was read from |
| `autoplay`, `loop` | off by default; autoplay is skipped when the reader prefers reduced motion |

Frames are baked as one sprite sheet plus per-frame timing; the kit draws them on a canvas with play/pause, a
scrubber and the caption of the current frame. There is no video element, so nothing starts on its own and nothing
needs a codec.

### Motion Canvas

```bash
npm create @motion-canvas@latest          # in media/src/flow
# author src/scenes/flow.tsx
```

Set the project background to *empty* (transparent) in **Video Settings**, resolution ~720 wide, frame rate 12, then
**RENDER → image sequence** (PNG). Point `bake.yaml` at the exported stills:

```yaml
anim:
  flow:
    frames: "media/src/flow/output/*.png"
    fps: 12
    width: 560
```

Headless projects can run their own command first:

```yaml
anim:
  flow:
    run: "npm --prefix media/src/flow run render"
    frames: "media/src/flow/output/*.png"
```

Draw with a transparent background and mid-tone colours: the card is read in both light and dark themes, and a raster
frame cannot follow the theme. Text baked into a frame is not searchable and does not scale with `--ex-scale` — another
reason to prefer a scene.

### Manim

Manim's product is a video; `bake` decodes it (`imageio[ffmpeg]`, part of the media extra):

```bash
cd media/src/flow && manim -ql --format=webm scene.py Walkthrough
```

```yaml
anim:
  flow:
    video: "media/src/flow/media/videos/**/Walkthrough.webm"
    fps: 10
    width: 560
```

Keep clips under ~10 seconds: 240 frames is the ceiling, and longer clips are subsampled, which loses timing.

## Bake, then validate

```bash
uv sync --extra media                       # once: pillow, vl-convert, imageio-ffmpeg (scenes need none of them)
atlas-explainer bake path/to/card           # renders frames, compiles charts, writes scenes
atlas-explainer bake path/to/card --only flow
atlas-explainer lint path/to/card           # also checks that baked media is current
```

`bake` runs only the commands you declare in `bake.yaml`; it never guesses at your toolchain. Commit the baked
`media/*.json` (and `*.webp` for animations) — a reader without the extras must still get a working card.

`lint` fails, rather than warning, when:

* an element names an asset that was never baked (`run atlas-explainer bake`);
* a source file changed after the bake (`stale — … changed after the last bake`);
* an `ex-scene` points at a chart or an animation, or an `ex-anim` at anything else;
* a scene breaks the rules above (one step, no title, unknown node, a step that changes nothing);
* the inlined media exceeds 2 MB (fewer frames, a narrower sheet, or a static chart);
* the element has no `caption`, or no `source`.

## Sizes

| Asset | Typical | Budget |
|---|---|---|
| scene, 8 nodes / 6 steps | 3–6 KB | 2 MB total per card |
| static chart, both themes | 25–60 KB | 〃 |
| interactive chart | +520 KB (the runtime) | 〃 |
| frame sheet, 560 px wide, 12 frames | 20–120 KB | 900 KB (quality steps down automatically) |

The page budget is 200 KB; baked media has its own 2 MB budget. A card of four scenes and a table fits in ~60 KB.