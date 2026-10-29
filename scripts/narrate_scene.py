"""Bake a neural-voice narration track for a scene card.

    uv run python scripts/narrate_scene.py <card-dir> [--voice zh-CN-XiaoxiaoNeural] [--rate +8%]

Reads the first (or --scene) scene in media/scenes/, speaks every step's title + detail with edge-tts,
re-encodes each clip to a small Opus file, and writes media/narration.json with one inline data URI per
frame. The kit plays that track instead of the browser's device voice; no network is needed at read time.

This is an authoring tool, not a runtime dependency: it needs network access, uvx and imageio-ffmpeg.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

try:
    import imageio_ffmpeg
except ImportError:  # pragma: no cover - optional authoring dependency
    imageio_ffmpeg = None


def scene_path(card: Path, name: str | None) -> Path:
    d = card / "media" / "scenes"
    if name:
        p = d / (name if name.endswith((".yaml", ".yml", ".json")) else name + ".yaml")
        if not p.is_file():
            sys.exit(f"scene not found: {p}")
        return p
    files = sorted(p for p in d.glob("*") if p.suffix.lower() in (".yaml", ".yml", ".json"))
    if not files:
        sys.exit(f"no scene under {d}; write media/scenes/<name>.yaml first")
    return files[0]


def ffmpeg() -> str:
    if imageio_ffmpeg is None:
        sys.exit("imageio-ffmpeg is missing; run uv sync --extra media")
    return imageio_ffmpeg.get_ffmpeg_exe()


def speak(text: str, voice: str, rate: str, out: Path) -> None:
    cmd = ["uvx", "edge-tts", "--voice", voice, "--rate", rate, "--text", text, "--write-media", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("edge-tts failed: " + (r.stderr or r.stdout).strip()[-800:])


def to_opus(src: Path, dst: Path, ff: str) -> None:
    cmd = [ff, "-y", "-loglevel", "error", "-i", str(src), "-c:a", "libopus", "-b:a", "16k", "-ac", "1", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed: " + (r.stderr or "").strip()[-800:])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("card", type=Path)
    ap.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    ap.add_argument("--rate", default="+8%")
    ap.add_argument("--scene", help="scene name (default: the first media/scenes/*.yaml)")
    args = ap.parse_args()

    card = args.card.resolve()
    src = scene_path(card, args.scene)
    raw = yaml.safe_load(src.read_text("utf-8"))
    steps = (raw or {}).get("steps") or []
    if not steps:
        sys.exit(f"{src}: no steps")
    ff = ffmpeg()
    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for i, step in enumerate(steps, 1):
            title = str(step.get("title") or "").strip()
            detail = str(step.get("detail") or "").strip()
            text = "。".join(x for x in (title, detail) if x)
            if not text:
                sys.exit(f"step {i} has no title/detail")
            mp3, ogg = t / f"{i}.mp3", t / f"{i}.ogg"
            print(f"[{i}/{len(steps)}] {text[:40]}...", flush=True)
            speak(text, args.voice, args.rate, mp3)
            to_opus(mp3, ogg, ff)
            frames.append({
                "text": text,
                "audio": "data:audio/ogg;base64," + base64.b64encode(ogg.read_bytes()).decode("ascii"),
            })
    payload = {
        "kind": "narration",
        "id": "narration",
        "voice": args.voice,
        "frames": frames,
        "baked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sources": {
            src.relative_to(card).as_posix(): hashlib.sha256(
                src.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()[:16],
        },
    }
    out = card / "media" / "narration.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", "utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(frames)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
