# Components

A card is `card.yaml` + `index.html`. The page links the kit by two fixed placeholders and contains no other script:

```html
<!doctype html>
<html>
<head><meta charset="utf-8"><title>…</title><link rel="stylesheet" href="atlas-kit:1.css"></head>
<body>
  …
<script src="atlas-kit:1.js"></script>
</body>
</html>
```

## card.yaml

```yaml
kit: 1
id: dataset-pipeline-walkthrough      # slug; must equal the directory name
title: …                              # ≤ 60 chars, plain text
questions:                            # the reader's own words, 1–12; used for search and de-duplication
  - parquet 里存的是什么？
summary: …                            # ≤ 200 chars, plain text, shown under the title in the panel
anchors:                              # files, symbols `path#Qual.name`, or `region:<id>`; must exist in the index
  - tools/dataset_pipeline/pipeline/stage1_build_row_index.py
tags: [pipeline]                      # optional, ≤ 8
language: zh
```

`apply` adds `anchor_hashes`, `run`, `at`. Never write them yourself.

## Tags

| Tag | Use | Rules |
|---|---|---|
| `<ex-qa q="…">…</ex-qa>` | one reader question and its answer — a chapter | `q` is the question in their words |
| `<ex-table source="real\|illustrative" origin="…" at="…" caption="…"><table>…</table></ex-table>` | a data sample | `source` required. `real` also requires `origin` (file, command or doc it was read from); `at` is when. Illustrative tables get a warning badge |
| `<ex-flow>` of `<ex-stage title="…" tag="path#symbol">` | one thing travelling through stages | each stage may hold `<ex-in>`, `<ex-out>`, `<ex-why>` plus free content; stages are numbered and collapsible; `title` required |
| `<ex-compare><ex-before label="…">…</ex-before><ex-after label="…">…</ex-after></ex-compare>` | before/after text | write plain text inside; words that differ are highlighted on both sides automatically |
| `<ex-anim src="atlas-media:<name>" source="…" origin="…" caption="…" autoplay loop>` | a baked frame animation — only for continuous motion | `caption` and `source` required; `source="real"` also needs `origin`; see [media.md](media.md) |
| `<ex-scene src="atlas-media:<name>" source="…" origin="…" caption="…">` | a click-through diagram: boxes, chips, arrows and values that change per step, each step with a title | the default way to show a process; steps are the explanation, prose shrinks to one sentence |
| `<ex-chart src="atlas-media:<name>" source="…" origin="…" caption="…" [interactive]>` | a baked Vega-Lite chart | `caption` and `source` required; `interactive` ships the Vega runtime (~500 KB) |
| `<a href="atlas://path/to/file.py#symbol">` | open that node on the map | only for nodes that exist |

Everything else is ordinary HTML: `h1`/`h2`/`h3`, `p`, `ul`/`ol`, `code`, `pre`, plain `table`, `strong`, `em`, inline
`style`, `<img src="data:image/…">`. Use `<p class="ex-lead">` for the grey lead-in under the title.

## Media

`ex-scene`, `ex-chart` and `ex-anim` do not contain their picture: they name a **baked asset** in `media/`, produced by
`atlas-explainer bake`. A scene is authored as `media/scenes/<name>.yaml`; a chart as a Vega-Lite spec; an animation
from stills or a video. Rules, schema and recipes are in [media.md](media.md).

Prefer a scene: it is the only one of the three whose text is live — themed, searchable and translated — and whose
steps the reader controls. Reach for a chart when the question is about quantity, and for an animation only when the
motion itself is the answer.

All three take the same provenance attributes as `ex-table` (`source`, `origin`, `at`), and lint requires them for the
same reason: a chart of numbers you did not read is a fabricated sample with axes.

## What lint rejects

other `<script>`s and `on…=` attributes; `fetch`/`XMLHttpRequest`/`WebSocket`/`eval`; `iframe`, `object`, `embed`, `form`,
`base`, `audio`, `video`; any URL leaving the card (`http(s):`, `//host`, `file:`, `javascript:`); CSS `@import` or external
`url()`; `ex-table` without a declared source; `ex-compare` missing a side; `ex-flow` with no stage; a packed card over
200 KB. Media adds: an `atlas-media:` name that was never baked, a baked asset whose sources changed since `bake`
(stale), a chart element pointing at an animation, a missing `caption`, a scene that breaks its rules (fewer than two
steps, a step with no title, a step that changes nothing, an unknown node id), and more than 2 MB of inlined media.
Run `codeatlas card validate` — its messages say which line.

## Layout notes

- The card is read in a ~46rem column inside a sandboxed frame; wide data goes in `ex-table` (it scrolls) or `pre`.
- Long lines (URLs) wrap in `pre`; shorten them with `…` and say so in the caption rather than dumping them.
- Light and dark themes follow the viewer automatically; do not hard-code colours.
