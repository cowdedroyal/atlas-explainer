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
| `<a href="atlas://path/to/file.py#symbol">` | open that node on the map | only for nodes that exist |

Everything else is ordinary HTML: `h1`/`h2`/`h3`, `p`, `ul`/`ol`, `code`, `pre`, plain `table`, `strong`, `em`, inline
`style`, `<img src="data:image/…">`. Use `<p class="ex-lead">` for the grey lead-in under the title.

## What lint rejects

other `<script>`s and `on…=` attributes; `fetch`/`XMLHttpRequest`/`WebSocket`/`eval`; `iframe`, `object`, `embed`, `form`,
`base`, `audio`, `video`; any URL leaving the card (`http(s):`, `//host`, `file:`, `javascript:`); CSS `@import` or external
`url()`; `ex-table` without a declared source; `ex-compare` missing a side; `ex-flow` with no stage; a packed card over
200 KB. Run `codeatlas card validate` — its messages say which line.

## Layout notes

- The card is read in a ~46rem column inside a sandboxed frame; wide data goes in `ex-table` (it scrolls) or `pre`.
- Long lines (URLs) wrap in `pre`; shorten them with `…` and say so in the caption rather than dumping them.
- Light and dark themes follow the viewer automatically; do not hard-code colours.
