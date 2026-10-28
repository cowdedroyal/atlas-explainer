# Media: animations and charts

Two kinds of answer need more than words and a table: **what happens in what order** (animation) and **how much,
compared to what** (chart). Both are baked into the card at authoring time, so the reader still gets one
self-contained page with no network and no scripts of its own.

```
media/
  bake.yaml          how to produce each asset (optional; conventions cover the common cases)
  src/<name>/        the animation: a Motion Canvas project, a Manim scene, or exported stills
  <name>.vl.json     the chart: a Vega-Lite spec; CSVs it reads sit next to it
  <name>.json        BAKED manifest — commit it
  <name>.webp        BAKED sprite sheet — commit it
```

Then in `index.html`:

```html
<ex-anim src="atlas-media:flow" source="real" origin="tools/pipeline/flow.mc" caption="…"></ex-anim>
<ex-chart src="atlas-media:throughput" source="real" origin="logs/run-2026-10-26.log" caption="…"></ex-chart>
```

## Choose the form

| The reader asks | Use |
|---|---|
| "what are the steps, and what goes in/out of each" | `<ex-flow>` / `<ex-stage>` — cheapest, searchable text |
| "in what order does it happen / why does X disappear here" | `<ex-anim>` |
| "how many, how often, how does it compare" | `<ex-chart>` |
| "…and I want to filter or zoom that" | `<ex-chart interactive>` |
| heavy math, 3D, a long procedural explanation | Manim → stills → `<ex-anim>` |

An animation is expensive: it is raster, it cannot be searched, it doubles the size of the card. Use it only when the
*order* or the *transition* is the point. If a still or a stage list answers the question, use that.

## An animation (`<ex-anim>`)

Render your scene to stills (or to a video), then bake:

| Attribute | Meaning |
|---|---|
| `src` | `atlas-media:<name>`; the asset baked from `media/src/<name>/` or `bake.yaml` |
| `caption` | **required** — the reader's text when the picture fails, and the frame's fallback label |
| `source`, `origin`, `at` | same rule as `ex-table`: `real` needs where it was read from |
| `autoplay`, `loop` | off by default; autoplay is skipped when the reader prefers reduced motion |

Baked frames are a grid of stills plus timing; the kit draws them on a canvas with play/pause, a scrubber, and the
caption of the current frame. There is no video element, so nothing starts on its own and nothing needs a codec.

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
    captions:
      - "clean: the empty category is filled from the label"
      - "filter: rows outside the taxonomy are dropped"
```

If your project has a headless render script, let `bake` run it first — that is what `run:` is for:

```yaml
anim:
  flow:
    run: "npm --prefix media/src/flow run render"
    frames: "media/src/flow/output/*.png"
```

Draw with a transparent background and mid-tone colours: the card is read in both light and dark themes, and a raster
frame cannot follow the theme. Text baked into a frame is not searchable and does not scale with `--ex-scale`, so keep
labels short and use the caption for the sentence.

### Manim

Manim's product is a video. `bake` decodes it (`imageio[ffmpeg]`, part of the media extra):

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

Use `-ql` (480p15) and keep clips short: 240 frames is the ceiling. Video `fps` is a target sampling rate, not a
playback speed: the baker reads the source timing and preserves the clip duration, including when subsampling.
If your version writes PNG frames, use `frames:` instead; for stills, set `fps` to the original export rate.
The baker may reduce frame dimensions to keep both sides of the WebP grid and decoded memory within limits.

### Any other tool

Anything that writes stills or a video works: `frames:` takes a glob, `video:` takes one file. Frame names must sort in
playback order (`000.png`, `001.png`, …).

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

* `data.url` is **inlined at bake time** from a file next to the spec (CSV or JSON). Source JSON files are separate
  from the referenced baked manifests. Remote URLs are rejected — a card
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

```html
<ex-chart src="atlas-media:throughput" interactive source="real" origin="logs/run.log" caption="…"></ex-chart>
```

That buys real Vega-Lite behaviour — hover tooltips, `params` selections, legend toggles, cross-filtering — under the
card's strict CSP: expressions are *interpreted* (`vega-interpreter`), never compiled with `new Function`, so no
`'unsafe-eval'` is needed.

Use it when the reader's question is "and what if I look at only these?" — not merely to have tooltips. Without the
flag the card is a static SVG of a few kilobytes; with it, half a megabyte, in every card that opts in.

## Bake, then validate

```bash
uv sync --extra media                       # once: pillow, vl-convert, imageio-ffmpeg
atlas-explainer bake path/to/card           # renders frames, compiles charts, writes media/*.json + *.webp
atlas-explainer bake path/to/card --only flow
atlas-explainer lint path/to/card           # also checks that baked media is current
```

`bake` runs only the commands you declare in `bake.yaml`; it never guesses at your toolchain. Commit the baked
`media/*.json` and `media/*.webp` — a reader without Pillow must still get a working card.

`lint` fails, rather than warning, when:

* an element names an asset that was never baked (`run atlas-explainer bake`);
* an animation sheet is missing, references a path outside `media/`, or is not a supported raster image;
* baked SVG contains scripts, event handlers, active elements, styles or external resource references;
* a source file changed after the bake (`stale — … changed after the last bake`);
* an `ex-anim` points at a chart or the other way round;
* the inlined media exceeds 2 MB (fewer frames, a narrower sheet, or a static chart);
* the element has no `caption`, or no `source`.

## Sizes

| Asset | Typical | Budget |
|---|---|---|
| frame sheet, 560 px wide, 12 frames, transparent | 20–120 KB | 900 KB (quality steps down automatically) |
| static chart, both themes | 25–60 KB | — |
| interactive chart | +520 KB (the runtime) | 2 MB total per card |

A card that shows both an animation and an interactive chart is around 700 KB packed. That is the price of an
explanation that cannot be abbreviated; a card with prose and a table stays under 30 KB.

Static SVG is displayed as an inert image, not inserted into the document as markup. Interactive cards carry the
Vega and vega-interpreter BSD license notices inside their single-file HTML output.
