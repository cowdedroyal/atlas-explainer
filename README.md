# atlas-explainer

Explainer cards for [Code Atlas](../code-atlas): visual answers to "I don't understand this part of the code",
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
| `src/atlas_explainer/kit/v1.css`, `v1.js` | the component kit: `ex-qa`, `ex-table`, `ex-flow`/`ex-stage`, `ex-compare` |
| `src/atlas_explainer/pack.py`, `cli.py` | `lint` (is the card safe and well-formed) and `pack` (inline the kit, add a CSP) |
| `skill/explain/` | the agent skill: when a card is worth making, how to get real samples, how to write one, which commands to run |
| `preview/host.html` | a stand-in for Code Atlas's reading layer: sandboxed iframe, theme/language/size messages |
| `examples/` | cards that pass lint and demonstrate every component |

Receiving cards — resolving anchors against the scanned index, staleness, `build`, the detail-panel list, the reading
layer — lives in Code Atlas. The two sides only share the manifest schema and the host protocol below.
Design: [code-atlas/docs/explainer-design.md](../code-atlas/docs/explainer-design.md).

## Install the skill

The skill is a plain Agent Skills folder. Copy it where your coding agent looks for skills, next to the `codeatlas` skill:

```bash
cp -r skill/explain ~/.claude/skills/explain          # Claude Code
cp -r skill/explain <repo>/.agents/skills/explain     # per-repository, for other agents
```

Then ask the agent a question about the code and say "make an explainer card for it" (or "沉淀成讲解卡"). It needs
`codeatlas` with the `card` commands (this repository's sibling `code-atlas`, version with explainer support).

## Try it

```bash
uv sync
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
| `<a href="atlas://path/to/file.py#symbol">` | asks the host to open that node on the map |

Everything else is ordinary HTML (headings, paragraphs, lists, `code`, `pre`, plain tables, inline `style`, `data:image/…`).
Lint rejects: other scripts or event handlers, network APIs, `iframe`/`object`/`form`/`base`, any URL that leaves the card
(`http(s):`, protocol-relative, `file:`, `javascript:`), CSS `@import`/external `url()`, tables without a declared source, and
packed cards over 200 KB.

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
