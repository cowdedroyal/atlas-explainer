"""`atlas-explainer lint|bake|pack` — every command prints JSON, like `codeatlas`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .media import BakeError, bake_card, bake_names
from .pack import card_dirs, lint_card, pack_card


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="atlas-explainer", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lint", help="check cards; exit 1 if any has problems")
    p.add_argument("path", nargs="+", type=Path, help="a card directory, or a directory containing card directories")
    p = sub.add_parser("bake", help="render animation frames and Vega-Lite charts into media/ (needs the media extra)")
    p.add_argument("path", nargs="+", type=Path)
    p.add_argument("--only", action="append", metavar="NAME",
                   help="bake just this asset (repeatable); the default is every asset the card declares")
    p = sub.add_parser("pack", help="lint, then write self-contained cards (kit, media and CSP inlined)")
    p.add_argument("path", nargs="+", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True, help="output directory; one subdirectory per card, plus index.json")
    args = ap.parse_args(argv)

    dirs = [d for p in args.path for d in card_dirs(p)]
    if not dirs:
        print(json.dumps({"ok": False, "error": "no card.yaml found"}))
        return 1
    if args.cmd == "bake":
        return _bake(dirs, args.only)
    if args.cmd == "lint":
        report = {d.name: lint_card(d) for d in dirs}
        ok = not any(report.values())
        print(json.dumps({"ok": ok, "cards": len(dirs), "problems": {k: v for k, v in report.items() if v}},
                         ensure_ascii=False, indent=2))
        return 0 if ok else 1
    index, problems = [], {}
    for d in dirs:
        errs = lint_card(d)
        if errs:
            problems[d.name] = errs
            continue
        try:
            index.append(pack_card(d, args.out / d.name))
        except (ValueError, OSError) as e:
            problems[d.name] = [str(e)]
    if problems:
        print(json.dumps({"ok": False, "problems": problems}, ensure_ascii=False, indent=2))
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "packed": [c["id"] for c in index], "out": str(args.out)}, ensure_ascii=False))
    return 0


def _bake(dirs: list[Path], only: list[str] | None) -> int:
    """Bake each card; `--only` narrows the work so one slow render does not redo the rest."""
    ok, report = True, {}
    for d in dirs:
        try:
            result = bake_card(d, only=set(only) if only else None)
        except BakeError as e:
            ok = False
            report[d.name] = {"ok": False, "error": str(e)}
            continue
        if only and not result["media"]:
            ok = False
            report[d.name] = {"ok": False, "error": f"nothing named {', '.join(only)}; this card declares "
                                                    f"{', '.join(bake_names(d)) or 'nothing'}"}
            continue
        report[d.name] = {"ok": True, "media": result["media"]}
    print(json.dumps({"ok": ok, "cards": report}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
