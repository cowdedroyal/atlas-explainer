"""Media: baking authored frames and Vega-Lite specs, and what lint/pack do with the result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from atlas_explainer.cli import main
from atlas_explainer.media import BakeError, bake_card
from atlas_explainer.pack import lint_card, load_media, pack_card, pack_html

PIL = pytest.importorskip("PIL.Image", reason="the media extra draws the fixture frames")
vl_convert = pytest.importorskip("vl_convert", reason="the media extra compiles the fixture charts")

HEAD = """<!doctype html>
<html><head><meta charset="utf-8"><title>demo</title>
<link rel="stylesheet" href="atlas-kit:1.css"></head><body>
"""
TAIL = """<script src="atlas-kit:1.js"></script></body></html>"""

MANIFEST = {"kit": 1, "id": "demo", "title": "Demo", "questions": ["what is this?"],
            "summary": "A card with media.", "anchors": ["demo.py"], "language": "en"}

ANIM = '<ex-anim src="atlas-media:flow" source="illustrative" caption="a moving dot"></ex-anim>'
CHART = '<ex-chart src="atlas-media:sales" source="illustrative" caption="counts"></ex-chart>'


def card(tmp_path: Path, body: str = ANIM) -> Path:
    d = tmp_path / "demo"
    (d / "media").mkdir(parents=True)
    (d / "card.yaml").write_text(yaml.safe_dump(MANIFEST), "utf-8")
    (d / "index.html").write_text(HEAD + body + TAIL, "utf-8")
    return d


def frames(d: Path, name: str = "flow", n: int = 6) -> Path:
    out = d / "media" / "src" / name / "frames"
    out.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        im = PIL.new("RGBA", (120, 60), (0, 0, 0, 0))
        im.paste(PIL.new("RGBA", (20, 20), (42, 111, 151, 255)), (i * 14, 20))
        im.save(out / f"{i:03d}.png")
    return out


def spec(d: Path, name: str = "sales") -> Path:
    p = d / "media" / f"{name}.vl.json"
    p.write_text(json.dumps({
        "data": {"url": f"{name}.csv"},
        "mark": "bar",
        "encoding": {"x": {"field": "k", "type": "nominal"},
                     "y": {"field": "n", "type": "quantitative"},
                     "tooltip": [{"field": "k"}, {"field": "n"}]},
    }), "utf-8")
    (d / "media" / f"{name}.csv").write_text("k,n\na,3\nb,7\n", "utf-8")
    return p


# ---- baking an animation ---------------------------------------------------

def test_bake_anim_writes_sheet_and_manifest(tmp_path):
    d = card(tmp_path)
    frames(d)
    assert bake_card(d)["media"]["flow"]["frames"] == 6
    manifest = json.loads((d / "media" / "flow.json").read_text("utf-8"))
    assert manifest["kind"] == "anim" and manifest["id"] == "flow"
    assert manifest["frames"] == 6 and manifest["columns"] == 3     # 560px wide frames: two rows of three
    assert manifest["sheet"] == "flow.webp"
    assert (d / "media" / "flow.webp").is_file()
    assert manifest["sources"]["media/src/flow/frames/000.png"]
    assert lint_card(d) == []


def test_bake_honours_fps_width_and_captions(tmp_path):
    d = card(tmp_path)
    frames(d, n=4)
    (d / "media" / "bake.yaml").write_text(
        "anim:\n  flow:\n    frames: media/src/flow/frames/*.png\n    fps: 4\n    width: 60\n    captions: [one, two]\n",
        "utf-8")
    bake_card(d)
    m = json.loads((d / "media" / "flow.json").read_text("utf-8"))
    assert m["fps"] == 4 and m["ms"] == 250
    assert (m["width"], m["height"]) == (60, 30)
    assert m["captions"] == ["one", "two"]          # short lists are allowed; the rest falls back to the caption


def test_long_animations_are_subsampled(tmp_path, monkeypatch):
    import atlas_explainer.media as media

    monkeypatch.setattr(media, "MAX_FRAMES", 3)
    d = card(tmp_path)
    frames(d, n=9)
    bake_card(d)
    m = json.loads((d / "media" / "flow.json").read_text("utf-8"))
    assert m["frames"] == 3 and m["fps"] == 4      # 12 fps / 3


def test_bake_needs_frames(tmp_path):
    d = card(tmp_path)
    (d / "media" / "src" / "flow").mkdir(parents=True)
    (d / "media" / "bake.yaml").write_text("anim:\n  flow:\n    frames: media/src/flow/frames/*.png\n", "utf-8")
    with pytest.raises(BakeError, match="no frames match"):
        bake_card(d)


def test_bake_reports_a_failed_command(tmp_path):
    d = card(tmp_path)
    (d / "media" / "bake.yaml").write_text("anim:\n  flow:\n    run: exit 2\n    frames: media/src/flow/frames/*.png\n", "utf-8")
    with pytest.raises(BakeError, match="exit 2"):
        bake_card(d)


def test_bake_rejects_unknown_config(tmp_path):
    d = card(tmp_path)
    (d / "media" / "bake.yaml").write_text("animation:\n  flow: {}\n", "utf-8")
    with pytest.raises(BakeError, match="unknown key"):
        bake_card(d)


def test_bake_rejects_one_name_for_two_kinds(tmp_path):
    d = card(tmp_path, ANIM + CHART.replace("sales", "flow"))
    frames(d, name="flow")
    spec(d, name="flow")
    with pytest.raises(BakeError, match="both an animation and a chart"):
        bake_card(d)


def test_bake_from_a_video(tmp_path):
    iio = pytest.importorskip("imageio.v3")
    d = card(tmp_path, '<ex-anim src="atlas-media:clip" source="illustrative" caption="clip"></ex-anim>')
    src = d / "media" / "src" / "clip"
    src.mkdir(parents=True)
    stills = [PIL.new("RGB", (64, 32), (i * 20, 80, 120)) for i in range(4)]
    iio.imwrite(src / "clip.gif", stills)
    (d / "media" / "bake.yaml").write_text(
        "anim:\n  clip:\n    video: media/src/clip/*.gif\n    fps: 5\n    width: 64\n", "utf-8")
    bake_card(d)
    m = json.loads((d / "media" / "clip.json").read_text("utf-8"))
    assert m["frames"] == 4 and m["fps"] == 5
    assert list(m["sources"])[0] == "media/src/clip/clip.gif"     # the video is the source, not its decoded stills
    assert lint_card(d) == []


# ---- lint sees what is missing, stale or mismatched -----------------------

def test_unbaked_media_is_a_lint_error(tmp_path):
    d = card(tmp_path)
    assert any("not baked" in p for p in lint_card(d))


def test_stale_media_is_rejected(tmp_path):
    d = card(tmp_path)
    frames(d)
    bake_card(d)
    assert lint_card(d) == []
    (d / "media" / "src" / "flow" / "frames" / "000.png").write_bytes(b"changed")
    problems = lint_card(d)
    assert any("stale" in p and "000.png" in p for p in problems), problems


def test_anim_and_chart_do_not_substitute_for_each_other(tmp_path):
    d = card(tmp_path, '<ex-chart src="atlas-media:flow" source="illustrative" caption="c"></ex-chart>')
    frames(d)                                        # bakes an `anim` called `flow`; the element wants a chart
    bake_card(d)
    assert any("needs a `chart` asset" in p for p in lint_card(d))


def test_media_needs_a_caption(tmp_path):
    d = card(tmp_path, '<ex-anim src="atlas-media:flow" source="illustrative"></ex-anim>')
    frames(d)
    bake_card(d)
    assert any("needs a caption" in p for p in lint_card(d))


def test_media_needs_a_name_and_a_source(tmp_path):
    d = card(tmp_path, '<ex-anim caption="x" source="illustrative"></ex-anim>')
    assert any('needs src="atlas-media:' in p for p in lint_card(d))


def test_media_name_is_a_slug(tmp_path):
    d = card(tmp_path, '<ex-anim src="atlas-media:../evil" caption="x" source="illustrative"></ex-anim>')
    assert any("letters, digits" in p for p in lint_card(d))


def test_media_size_is_budgeted(tmp_path, monkeypatch):
    import atlas_explainer.pack as pack

    d = card(tmp_path)
    frames(d)
    bake_card(d)
    monkeypatch.setattr(pack, "MAX_MEDIA_BYTES", 100)
    assert any("inlined media is" in p for p in lint_card(d))


def test_broken_manifest_is_reported(tmp_path):
    d = card(tmp_path)
    frames(d)
    bake_card(d)
    (d / "media" / "flow.json").write_text("{not json", "utf-8")
    assert any("not valid JSON" in p for p in lint_card(d))


# ---- packing: the page carries the media, nothing points outside ----------

def test_pack_inlines_the_sheet_and_the_registry(tmp_path):
    d = card(tmp_path)
    frames(d)
    bake_card(d)
    pack_card(d, tmp_path / "out")
    html = (tmp_path / "out" / "index.html").read_text("utf-8")
    assert 'id="atlas-media-registry"' in html
    assert "data:image/webp;base64," in html
    assert "atlas-media:flow" in html            # the element still names the entry; the kit resolves it
    assert "vega.min.js" not in html             # no runtime for a card that has no interactive chart


def test_pack_without_media_arguments_refuses_to_drop_pictures(tmp_path):
    d = card(tmp_path)
    frames(d)
    bake_card(d)
    with pytest.raises(ValueError, match="baked media"):
        pack_html((d / "index.html").read_text("utf-8"), MANIFEST)


# ---- charts ---------------------------------------------------------------

def test_bake_chart_writes_both_themes(tmp_path):
    d = card(tmp_path, CHART)
    spec(d)
    bake_card(d)
    m = json.loads((d / "media" / "sales.json").read_text("utf-8"))
    assert set(m["svg"]) == {"light", "dark"}
    assert m["svg"]["light"].startswith("<svg")
    assert m["vega"] is None                      # static unless bake.yaml asks for interaction
    assert m["tooltip"] == ["k", "n"]
    assert lint_card(d) == []


def test_chart_data_is_inlined(tmp_path):
    d = card(tmp_path, CHART)
    spec(d)
    bake_card(d)
    m = json.loads((d / "media" / "sales.json").read_text("utf-8"))
    assert "sales.csv" not in json.dumps(m["svg"])
    assert "a" in m["svg"]["light"]


def test_interactive_chart_ships_the_runtime(tmp_path):
    d = card(tmp_path, '<ex-chart src="atlas-media:sales" source="illustrative" caption="c" interactive></ex-chart>')
    spec(d)
    (d / "media" / "bake.yaml").write_text("chart:\n  sales:\n    interactive: true\n", "utf-8")
    bake_card(d)
    m = json.loads((d / "media" / "sales.json").read_text("utf-8"))
    assert set(m["vega"]) == {"light", "dark"}
    pack_card(d, tmp_path / "out")
    html = (tmp_path / "out" / "index.html").read_text("utf-8")
    assert "vegaInterpreter" in html and "window.vega" in html
    assert "'unsafe-eval'" not in html           # interpreted expressions, not compiled ones


def test_chart_with_missing_data_file_fails(tmp_path):
    d = card(tmp_path, CHART)
    spec(d)
    (d / "media" / "sales.csv").unlink()
    with pytest.raises(BakeError, match="sales.csv"):
        bake_card(d)


def test_chart_with_remote_data_is_refused(tmp_path):
    d = card(tmp_path, CHART)
    (d / "media" / "sales.vl.json").write_text(json.dumps({"data": {"url": "https://example.test/a.csv"}, "mark": "bar"}),
                                              "utf-8")
    with pytest.raises(BakeError, match="remote"):
        bake_card(d)


def test_broken_spec_is_reported_with_the_spec_name(tmp_path):
    d = card(tmp_path, CHART)
    (d / "media" / "sales.vl.json").write_text(json.dumps({"mark": "nonsense"}), "utf-8")
    with pytest.raises(BakeError, match="sales.vl.json"):
        bake_card(d)


# ---- CLI ------------------------------------------------------------------

def test_cli_bake_only_narrows_the_work(tmp_path, capsys):
    d = card(tmp_path, ANIM + CHART)
    frames(d)
    spec(d)
    assert main(["bake", str(d), "--only", "flow"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert list(out["cards"]["demo"]["media"]) == ["flow"]
    assert not (d / "media" / "sales.json").exists()
    assert main(["bake", str(d)]) == 0
    assert (d / "media" / "sales.json").exists()


def test_cli_bake_reports_a_bad_card(tmp_path, capsys):
    d = card(tmp_path)
    assert main(["bake", str(d)]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_cli_pack_refuses_a_stale_card(tmp_path, capsys):
    d = card(tmp_path)
    frames(d)
    bake_card(d)
    (d / "media" / "src" / "flow" / "frames" / "000.png").write_bytes(b"changed")
    assert main(["pack", str(d), "-o", str(tmp_path / "out")]) == 1
    assert "stale" in capsys.readouterr().out


def test_load_media_ignores_specs(tmp_path):
    d = card(tmp_path, CHART)
    spec(d)
    bake_card(d)
    media, errors = load_media(d)
    assert errors == [] and list(media) == ["sales"]
