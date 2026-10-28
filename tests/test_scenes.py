"""Scenes: a click-through diagram drawn by the kit, with no media extra and no renderer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from atlas_explainer.cli import main
from atlas_explainer.media import BakeError, bake_card, normalize_scene, validate_scene
from atlas_explainer.pack import lint_card, load_media, pack_card

HEAD = """<!doctype html>
<html><head><meta charset="utf-8"><title>demo</title>
<link rel="stylesheet" href="atlas-kit:1.css"></head><body>
"""
TAIL = """<script src="atlas-kit:1.js"></script></body></html>"""
MANIFEST = {"kit": 1, "id": "demo", "title": "Demo", "questions": ["how does it flow?"],
            "summary": "A card with a scene.", "anchors": ["demo.py"], "language": "en"}
SCENE = '<ex-scene src="atlas-media:flow" source="illustrative" caption="a row through two stages"></ex-scene>'

YAML_SCENE = """
size: [640, 240]
nodes:
  - {id: row, kind: chip, text: A-1, sub: "empty", at: [20, 90], size: [110, 40]}
  - {id: clean, kind: box, text: clean, sub: "stage 0", at: [180, 80], size: [120, 60]}
  - {id: done, kind: box, text: done, at: [340, 80], size: [120, 60]}
  - {id: sum, kind: label, text: "3 rows", at: [520, 110]}
edges:
  - {from: clean, to: done, dashed: true}
steps:
  - title: "A row arrives"
    detail: "Its category is empty, so it cannot be routed yet."
    show: [row]
    focus: [row]
  - title: "clean fills it in"
    show: [clean]
    move: {row: [184, 90]}
    sub: {row: "shoes"}
  - title: "Done"
    show: [done, sum]
    tone: {done: ok}
    focus: []
"""


def card(tmp_path: Path, body: str = SCENE) -> Path:
    d = tmp_path / "demo"
    (d / "media").mkdir(parents=True)
    (d / "card.yaml").write_text(yaml.safe_dump(MANIFEST), "utf-8")
    (d / "index.html").write_text(HEAD + body + TAIL, "utf-8")
    return d


def scene_source(d: Path, text: str = YAML_SCENE, name: str = "flow") -> Path:
    p = d / "media" / "scenes" / f"{name}.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, "utf-8")
    return p


def test_bake_scene_writes_a_small_manifest(tmp_path):
    d = card(tmp_path)
    scene_source(d)
    written = bake_card(d)["media"]["flow"]
    assert written["kind"] == "scene" and written["steps"] == 3
    manifest = json.loads((d / "media" / "flow.json").read_text("utf-8"))
    assert manifest["kind"] == "scene" and manifest["id"] == "flow"
    assert manifest["scene"]["nodes"][0]["id"] == "row"
    assert manifest["sources"]["media/scenes/flow.yaml"]
    assert (d / "media" / "flow.json").stat().st_size < 8_000
    assert lint_card(d) == []


def test_scene_json_source_works_too(tmp_path):
    d = card(tmp_path)
    src = d / "media" / "scenes" / "flow.json"
    src.parent.mkdir(parents=True)
    src.write_text(json.dumps(yaml.safe_load(YAML_SCENE)), "utf-8")
    assert bake_card(d)["media"]["flow"]["steps"] == 3


def test_scene_needs_a_source(tmp_path):
    d = card(tmp_path)
    (d / "media" / "bake.yaml").write_text("scene:\n  flow: {}\n", "utf-8")
    with pytest.raises(BakeError, match="no scene source"):
        bake_card(d)


def test_scene_needs_two_steps(tmp_path):
    d = card(tmp_path)
    scene_source(d, YAML_SCENE.split("  - title: \"clean fills it in\"")[0] + "    sub: {row: shoes}\n")
    with pytest.raises(BakeError, match="2–12"):
        bake_card(d)


def test_every_step_needs_a_title(tmp_path):
    d = card(tmp_path)
    scene_source(d, YAML_SCENE.replace('  - title: "Done"', "  - title: \"\""))
    with pytest.raises(BakeError, match="needs a title"):
        bake_card(d)


def test_a_step_must_change_or_explain_something(tmp_path):
    d = card(tmp_path)
    scene_source(d, YAML_SCENE.replace('  - title: "Done"\n    show: [done, sum]\n    tone: {done: ok}\n    focus: []',
                                       '  - title: "Done"'))
    with pytest.raises(BakeError, match="pointless"):
        bake_card(d)


def test_scene_rejects_unknown_nodes_and_tones(tmp_path):
    d = card(tmp_path)
    scene_source(d, YAML_SCENE.replace("move: {row: [184, 90]}", "move: {ghost: [1, 2]}"))
    with pytest.raises(BakeError, match="unknown node"):
        bake_card(d)
    scene_source(d, YAML_SCENE.replace("tone: {done: ok}", "tone: {done: purple}"))
    with pytest.raises(BakeError, match="tone"):
        bake_card(d)


def test_scene_names_must_be_unique_per_kind(tmp_path):
    d = card(tmp_path, SCENE + '<ex-chart src="atlas-media:flow" source="illustrative" caption="c"></ex-chart>')
    scene_source(d)
    (d / "media" / "flow.vl.json").write_text(json.dumps({"data": {"values": [{"a": 1}]}, "mark": "bar"}), "utf-8")
    with pytest.raises(BakeError, match="declared as both"):
        bake_card(d)


def test_pack_carries_the_scene_as_data(tmp_path):
    d = card(tmp_path)
    scene_source(d)
    bake_card(d)
    pack_card(d, tmp_path / "out")
    html = (tmp_path / "out" / "index.html").read_text("utf-8")
    assert 'id="atlas-media-registry"' in html and '"kind":"scene"' in html
    assert "data:image/" not in html.split('id="atlas-media-registry"')[1].split("</script>")[0]
    assert len(html) < 60_000          # the inlined kit dominates a one-page card


def test_lint_rejects_an_unbaked_scene(tmp_path):
    d = card(tmp_path)
    assert any("not baked" in p for p in lint_card(d))


def test_a_tampered_manifest_is_rejected(tmp_path):
    d = card(tmp_path)
    scene_source(d)
    bake_card(d)
    manifest = json.loads((d / "media" / "flow.json").read_text("utf-8"))
    manifest["scene"]["steps"][0]["title"] = ""
    (d / "media" / "flow.json").write_text(json.dumps(manifest), "utf-8")
    assert any("needs a title" in p for p in lint_card(d))


def test_validate_scene_accepts_defaults():
    scene = normalize_scene({"nodes": [{"id": "a", "text": "x"}],
                             "steps": [{"title": "one", "detail": "why"}, {"title": "two", "show": ["a"]}]})
    assert scene["size"] == [720, 300]
    assert scene["nodes"][0]["kind"] == "box"
    assert validate_scene(scene) == []


def test_validate_scene_reports_several_problems_at_once():
    scene = normalize_scene({"nodes": [{"id": "1bad", "kind": "blob", "at": [9000, 0], "tone": "loud"}],
                             "steps": [{"title": "x", "show": ["nope"]}, {"title": "y", "detail": "z"}]})
    errors = validate_scene(scene)
    assert len(errors) >= 4 and any("id must start" in e for e in errors)


def test_cli_bake_only_scene(tmp_path, capsys):
    d = card(tmp_path)
    scene_source(d)
    assert main(["bake", str(d), "--only", "flow"]) == 0
    assert json.loads(capsys.readouterr().out)["cards"]["demo"]["media"]["flow"]["kind"] == "scene"
