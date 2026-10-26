# Getting real samples

A card is believable only if its numbers and rows are. Collect them before writing, keep a note of where each came from, and
put that in `origin`.

## What counts as a real sample

| Source | Example `origin` |
|---|---|
| a data file read by a short script | `data/x.parquet, read with pyarrow 2026-10-26` |
| a measurement you ran | `measured: ran pipeline/openvab_index.py on data/x.parquet` |
| a log or report in the repo | `docs/report.md §3` |
| a number quoted from documentation | `tools/…/README.md「全量实测」` — say it is the doc's figure, not yours |
| a cached intermediate | `data/…/build/llm_cache.jsonl` |

If you could not read it, it is `illustrative`. A table half real and half invented is `illustrative`, with the real
part named in the caption.

## Doing it safely

- **Read-only, bounded.** Use a short throwaway script in a scratch directory outside the repository (`python -I`).
  Read only the columns and rows you need; print counts and a handful of rows, not the dataset.
- **Do not run the pipeline** to produce a sample, and do not touch private storage (S3/COS/databases) unless the
  user has said it is fine. Credentials never appear in a script you write or a card you save.
- **Windows consoles are not UTF-8.** Set `PYTHONIOENCODING=utf-8` (or `sys.stdout.reconfigure(encoding="utf-8")`) and
  write output to a file; otherwise Chinese or other non-ASCII data prints as garbage and you will misread it.
- **Measure rather than estimate** when you can: file sizes, row counts, distinct values. Re-run a transformation on the
  real input if the repository ships it (into a scratch path) — a measured before/after beats a documented one.
- **Verify round trips.** If a card claims a transformation is lossless or reversible, check it on real rows.

## Trust but compare

The data on disk may already be post-processed, truncated, a different version, or missing (it is often gitignored on
other machines). Before writing "the file contains X", compare what you read against what the code says should be
there. Typical outcomes worth stating in the card:

- the cleaning step ran already, so the dirty rows it removes are no longer present — show the rule and the *after*
  state, and say the *before* comes from the code;
- the number in the documentation was measured on a different dataset or date — quote it as such;
- an intermediate the explanation depends on (scan shards, caches) is not on this machine — say what you could not look at.

## Sanitising

Cards are committed and may be pushed. Before saving:

- elide bucket names, internal hostnames and signed/query-string URLs (`s3://<bucket>/…`); keep the path *shape* if
  that is the point;
- no tokens, passwords, personal data;
- identifiers that exist only in private data (user ids, order ids) — use them only if the repository already
  commits them, otherwise keep a few and tell the user.
