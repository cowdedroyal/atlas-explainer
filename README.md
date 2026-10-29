# atlas-explainer

Explainer cards for [Code Atlas](https://github.com/cowdedroyal/code-atlas): visual answers to "I don't understand this part of the code",
kept in the repository so the next reader doesn't have to ask again.

A **card** is a small directory under `.codemap/explainers/<id>/`:

```text
card.yaml    who asked what, and which files/symbols/regions the card explains
index.html   the explanation: one self-contained page written with the component kit
```

This repository holds the pieces that authors and agents need, independent of the viewer:

| Path | What |
|---|---|
| `src/atlas_explainer/card.schema.json` | JSON Schema of `card.yaml` (kit 1) |
| `src/atlas_explainer/kit/v1.css`, `v1.js` | the component kit: `ex-qa`, `ex-table`, `ex-flow`/`ex-stage`, `ex-compare`, `ex-anim`, `ex-chart` |
| `src/atlas_explainer/pack.py`, `cli.py` | `lint` (is the card safe and well-formed), `bake` (frames and charts), `pack` (inline the kit and media, add a CSP) |
| `src/atlas_explainer/media.py` | turning authored animation sources and Vega-Lite specs into what a card can carry |
| `src/atlas_explainer/media/vendor/` | the Vega runtime that interactive charts are inlined with (BSD-3, see its README) |
| `skill/explain/` | the flow skill: locate the tour step the reader is stuck on, keep the tour accurate at function level, and hang a small step-through card on each step (no autoplay); lead + subagents build steps in parallel |
| `preview/host.html` | a stand-in for Code Atlas's reading layer: sandboxed iframe, theme/language/size messages |
| `examples/` | cards that pass lint and demonstrate every component |

Receiving cards — resolving anchors against the scanned index, staleness, `build`, the detail-panel list, the reading
layer — lives in Code Atlas. The two sides only share the manifest schema and the host protocol below.
Design: [code-atlas/docs/explainer-design.md](https://github.com/cowdedroyal/code-atlas/blob/feat/explainer-cards/docs/explainer-design.md).

## Install the skill

The skill is a plain Agent Skills folder. Copy it where your coding agent looks for skills, next to the `codeatlas` skill:

```bash
cp -r skill/explain ~/.claude/skills/explain          # Claude Code
cp -r skill/explain <repo>/.agents/skills/explain     # per-repository, for other agents
```

Then point the agent at a flow: say "把这条流程讲清楚" / "这一步没懂" (or "沉淀成一条流程"). It needs
`codeatlas` with the `tour` and `card` commands (this repository's sibling `code-atlas`).

If the explanation is one giant page — or the tour stops at file level — say "把这条流程做成讲解" / "make this flow
explainable". The `explain` skill works one level up: a Code Atlas **tour** (an ordered walk through the code, each
step a function) is the unit, and each step gets its own small step-through card, so the reader opens one step at a
time instead of one giant page. Tours are validated for connectivity and for the card hanging on the right step; cards
are validated per frame (overlaps, caption length, label budget, no autoplay, ≤80 KB). Readability is bought with more
frames, never by shortening sentences or moving prose into the figure. A lead agent can fan the steps out to several
subagents, and two newcomers must retell the flow step by step before it is accepted.

## Try it

```bash
uv sync                                    # lint/pack only
uv sync --extra media                      # + bake: pillow, vl-convert, imageio-ffmpeg
uv run atlas-explainer bake examples       # only needed after editing media sources
uv run atlas-explainer lint examples
uv run atlas-explainer pack examples -o dist/cards
uv run python -m http.server 8790          # then open http://localhost:8790/preview/host.html
uv run pytest
```

## Writing a card

The page links the kit through two fixed placeholders and contains no other script:

```html
<link rel="stylesheet" href="atlas-kit:1.css">
…
<script src="atlas-kit:1.js"></script>
```

| Element | Use |
|---|---|
| `<ex-qa q="reader's question">…</ex-qa>` | a question and its answer; one chapter of the card |
| `<ex-table source="real" origin="…" at="…"><table>…</table></ex-table>` | a data sample. `source` is **required**: `real` (also needs `origin`: the file, command or log it was read from) or `illustrative` (shown with a warning badge) |
| `<ex-flow><ex-stage title tag><ex-in>…</ex-in><ex-out>…</ex-out><ex-why>…</ex-why></ex-stage>…</ex-flow>` | the same data travelling through stages: input, output and the reason, collapsible, numbered |
| `<ex-compare><ex-before>…</ex-before><ex-after>…</ex-after></ex-compare>` | before/after text; the words that changed are highlighted on both sides |
| `<ex-scene src="atlas-media:name" source="…" caption="…">` | a diagram the reader clicks through: labelled boxes, arrows and per-step payloads that change; each click is one sentence of explanation |
| `<ex-anim src="atlas-media:name" source="…" caption="…" autoplay loop>` | a baked frame animation — only for continuous motion |
| `<ex-chart src="atlas-media:name" source="…" caption="…" interactive>` | a baked Vega-Lite chart; `interactive` keeps tooltips, selections and legend toggles |
| `<a href="atlas://path/to/file.py#symbol">` | asks the host to open that node on the map |

Everything else is ordinary HTML (headings, paragraphs, lists, `code`, `pre`, plain tables, inline `style`, `data:image/…`).
Lint rejects: other scripts or event handlers, network APIs, `iframe`/`object`/`form`/`base`, any URL that leaves the card
(`http(s):`, protocol-relative, `file:`, `javascript:`), CSS `@import`/external `url()`, tables without a declared source,
`atlas-media:` names that were never baked or that changed since the bake, and packed cards over 200 KB.

## Scenes, charts and animations

Text and tables cannot show *what changes between two states*, *how much against what*, or *continuous motion*. Those
get baked media, because the tools behind them are either too heavy for a reader with no network and no scripts of its
own, or would bake the explanation into pixels:

| Form | Written as | What the reader gets |
|---|---|---|
| `<ex-scene>` **(default)** | `media/scenes/<name>.yaml` | boxes, chips, arrows and values drawn as live SVG; each click reveals a step, changes a payload and prints one sentence |
| `<ex-chart>` | `media/<name>.vl.json` (Vega-Lite, BSD) | an inline SVG chart per theme, or a real interactive Vega view |
| `<ex-anim>` | stills from [Motion Canvas](https://github.com/motion-canvas/motion-canvas) (MIT) or Manim (MIT), or a video | a frame player — for motion that has no discrete steps |

A scene is the form to reach for: it is a few kilobytes, its text is searchable, themed and translated, and the reader
stops where they want. A video is the last resort: it cannot be stopped at a step, and it costs hundreds of kilobytes.

```
card/
  card.yaml
  index.html           <ex-scene src="atlas-media:clean-pipeline">, <ex-chart src="atlas-media:throughput">
  media/
    scenes/clean-pipeline.yaml   authored: nodes, edges, steps            ← the explanation itself
    clean-pipeline.json          baked manifest (commit)
    throughput.vl.json           authored Vega-Lite spec; CSVs sit next to it
    throughput.json              baked: SVG per theme, compiled Vega spec (commit)
```

```bash
uv run atlas-explainer bake path/to/card            # write scenes, compile charts, render frames
uv run atlas-explainer bake path/to/card --only flow
uv run atlas-explainer lint path/to/card            # also: is the baked media current?
```

Two details make this safe: the sheet becomes a `data:` URI inside the page (images and canvas only, no `video`), and
interactive charts run Vega through `vega-interpreter` rather than `new Function`, so the card's CSP keeps
`script-src 'unsafe-inline'` without `'unsafe-eval'`. The runtime is vendored once in
`src/atlas_explainer/media/vendor/` and inlined only into cards that ask for it.

Sizes: a scene is 3–6 KB, a 12-frame sheet 20–120 KB, a static chart 25–60 KB, an interactive chart about 550 KB. The
page budget stays 200 KB; baked media has its own 2 MB budget. The scene schema and recipes for charts, Motion Canvas
and Manim are in [skill/explain/references/builder.md](skill/explain/references/builder.md).

## Neural narration

A card with a stepper or a scene gets a **放映** button: it plays every frame, reads the caption, and advances when
the clip ends. Without extra files it uses the reader's device voice. To use a natural voice instead, bake one clip per
frame into `media/narration.json`:

```bash
uvx edge-tts --list-voices
uv run python scripts/narrate_scene.py path/to/card --voice zh-CN-XiaoxiaoNeural --rate +8%
```

The script speaks each scene step's title + detail with [edge-tts](https://github.com/rany2/edge-tts), re-encodes the
clips to 16 kbps Opus (so six steps stay around 150 KB), and writes one `data:audio/ogg` URI per frame. Playback is
then fully offline; `media-src data:` is the only CSP addition. Re-run the script after editing a step's text.

[`examples/renderer-imports`](examples/renderer-imports) contains real Motion Canvas PNG exports and a Manim MP4,
with their scene source. Video sampling preserves source duration; the sheet grid bounds both dimensions and
decoded memory. Media validation rejects missing images, escaping paths, active SVG and external resource URLs.
Static SVG is displayed as an inert image, and standalone interactive pages retain the runtime's BSD notices.

For the browser regression check, pack the examples and run
`node scripts/check_media_browser.cjs <packed-dir>` with Playwright installed. `PLAYWRIGHT_MODULE` can point at an
existing Playwright module and `CHROMIUM_EXECUTABLE_PATH` at an existing Chromium executable.

## Host protocol

The viewer runs the packed page in `<iframe sandbox="allow-scripts">` (no `allow-same-origin`); the page's own CSP forbids
all network access. Messages, all via `postMessage`:

| Direction | Message |
|---|---|
| host → card | `{type:"atlas:theme", theme:"light"\|"dark", lang:"zh", scale:1.0}` |
| card → host | `{type:"atlas:ready", kit:1}` after load |
| card → host | `{type:"atlas:height", height:<px>}` whenever the content size changes |
| card → host | `{type:"atlas:open", target:"<path>#<symbol>"}` when an `atlas://` link is clicked |

Without a host the card follows the system light/dark preference.

`preview/host.html` loads a card with `fetch` + `iframe.srcdoc` rather than `iframe.src`: the viewer is a static site
and needs no extra route, and some embedded browsers refuse to navigate sub-frames by URL. A `srcdoc` document also
inherits the embedding page's CSP, so the viewer's own policy must not be stricter than the card's.

## License

Apache-2.0 — see [LICENSE](LICENSE).
