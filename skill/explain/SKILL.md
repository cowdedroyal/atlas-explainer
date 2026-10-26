---
name: explain
description: Answer "I don't understand this part of the code/data" with a visual explainer card that Code Atlas keeps on the map. Use when the user asks you to explain how some code, data format or pipeline stage works, asks "why does X do Y", wants an example walked through, or says to remember/save/keep an explanation ("沉淀", "做成讲解卡", "explain card"). Produces a card under `.codemap/explainers/` that shows up in the detail panel of the files, symbols and regions it explains.
---

# explain: answers that stay on the map

A reader got stuck on something in this repository. You answer them — and when the answer needs a worked
example, a picture of the data, or will be asked again, you also leave a **card**: a small visual page hung on the code
it explains, stored in `.codemap/explainers/<id>/` and committed with the rest of the map. The next person who clicks that
file in Code Atlas sees it.

The chat answer always comes first and stands on its own. The card is the durable, richer version.

## When a card is worth making

Make one when at least one is true: the answer needs real data or a before/after to be believable; it follows
something through several stages; the confusion is likely to repeat for the next reader. Do **not** make one for a
one-line answer, a pure opinion, or something the code's own docstring already says well — say so and answer in chat.

## Procedure

1. **Look for an existing card.** `codeatlas card search "<their words>"` and `--anchor <file or symbol>`. If one
   covers the same storyline, update it (same `id`) instead of adding a second.
2. **Locate and read.** Use `codeatlas show`, `context`, `path` to find the nodes, then read the actual code. Never
   explain from names alone. Keep notes of `path:line` for each claim you will make.
3. **Get real samples.** Read the real data the user is asking about ([references/sampling.md](references/sampling.md)):
   a few rows, a schema, a log line, a measured size. Record where each came from. Where you cannot read it, say
   so and mark it illustrative.
4. **Find the through-line.** If the user asked several questions, they are usually one thing — a piece of data
   travelling through stages. Pick a single running example and make each question a chapter
   ([references/narrative.md](references/narrative.md)).
5. **Write the card** in a drafts directory *outside* the mapped repository (so drafts do not become map nodes):
   `card.yaml` + `index.html`, using only the kit's tags ([references/components.md](references/components.md)).
6. **Validate, fix, apply.** `codeatlas card validate DIR`; read every error and fix the content — never
   weaken a source declaration or drop an anchor just to pass. Then `codeatlas card apply DIR`.
7. **Check it is trackable.** Run `git check-ignore -v .codemap/explainers/<id>/card.yaml`. If the repository's
   `.gitignore` swallows `.codemap/`, tell the user — the card will not reach the remote until they allow it. Do not edit
   their `.gitignore` unasked.
8. **Reply** in two or three sentences: the card's title, which nodes it hangs on, how to open it
   (`codeatlas serve -r <repo>`, then click the node → Explanations). Mention anything you could not verify.

## Hard rules

1. **Real means read.** `<ex-table source="real" origin="…">` only for data you actually read, with `origin` naming the
   file, command or log (and, for a doc figure, the doc). Anything composed by you is `source="illustrative"`.
   A fabricated sample that looks real is the worst failure this format has.
2. **The data on disk may not be the data the code describes.** Cleaning steps, migrations and caches mean the
   current file can already be post-processed. Compare what you read with what the code says should be there, and
   say so in the card when they differ ("this copy is already cleaned, so the dirty rows no longer exist locally").
3. **Separate what you read from what you infer.** Anything the repository does not record (why something was
   done, who decided) is phrased as inference or left out. Correct the reader's misconception plainly when their
   mental model is off — that is often the whole value of the card.
4. **Read-only and credential-free.** Do not write to datasets, run pipeline stages, or call private storage /
   network services to get samples without the user's say-so. Never put secrets, tokens, signed URLs, private
   hostnames or personal data into a card — it is committed and may be pushed. Shorten or elide internal URLs and
   bucket names; keep the structure that matters.
5. **One storyline per card, one running example.** Chapters answer questions; the reader should be able to
   retell the flow afterwards without opening the code.
6. **Anchors are what the card explains**, not everything it mentions: files, symbols (`path#Qual.name`) or
   `region:<id>` that exist in the index. A card on a class also appears on its methods.
7. **Write in the configured language** (`.codemap/config.yaml` → `language`); keep identifiers, paths and data
   values exactly as they are.
8. **Do not change source, the structure index or built JSON** to make an explanation true. If you find a real
   problem in the code, say so in chat and offer to handle it separately.
9. **Keep it small.** A packed card over 200 KB is rejected; tables show a few rows, not dumps.

## Commands

| Command | Use |
|---|---|
| `codeatlas card search [QUERY] [--anchor NODE]` | find cards by words or by what they explain |
| `codeatlas card validate DIR` | lint the page and check every anchor exists (dry run) |
| `codeatlas card apply DIR` | write it to `.codemap/explainers/<id>/`; same id replaces; identical content changes nothing |
| `codeatlas card confirm ID` | after reviewing a stale card against the current code |
| `codeatlas card delete ID` | remove (revertible with `codeatlas revert <run>`) |
| `codeatlas agenda --type refresh` | lists stale cards (`card:<id>`) with the nodes that changed |

When a card is stale, re-read the changed code, fix the card if it is now wrong (apply), or `confirm` it if it is still
true.
