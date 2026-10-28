"""Draw the frames of the example animation (illustrative data, transparent background).

The demo card ships these stills so that `atlas-explainer bake` can be run on a fresh clone without installing
Motion Canvas or Manim. A real card renders its scene with one of those tools instead — see skill/explain/references/media.md.

    python media/src/flow/gen.py     # from the card directory
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, N = 400, 180, 12
OUT = Path(__file__).parent / "frames"
INK = (91, 143, 185, 255)          # mid tone: readable on the light and the dark card
MUTED = (140, 148, 160, 255)
CHIP = (224, 122, 95, 255)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=12)
    for i in range(N):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for j, (label, x) in enumerate((("clean", 18), ("filter", 148), ("normalize", 278))):
            d.rounded_rectangle([x, 40, x + 104, 104], radius=8, outline=INK, width=2)
            d.text((x + 10, 46), label, font=font, fill=INK)
            d.text((x + 10, 88), f"stage {j}", font=font, fill=MUTED)
        t = i / (N - 1)
        x = 8 + t * 292
        d.rounded_rectangle([x, 56, x + 64, 80], radius=6, fill=INK)
        d.text((x + 8, 61), "A-1001", font=font, fill=(255, 255, 255, 255))
        fade = max(0.0, min(1.0, 1.0 - (t - 0.45) / 0.25))     # the row the second stage removes
        if fade > 0:
            y = int(126 - 20 * t)
            d.rounded_rectangle([x, y, x + 64, y + 24], radius=6, fill=CHIP[:3] + (int(255 * fade),))
            d.text((x + 8, y + 5), "A-1003", font=font, fill=(255, 255, 255, int(255 * fade)))
        im.save(OUT / f"{i:03d}.png")


if __name__ == "__main__":
    main()
