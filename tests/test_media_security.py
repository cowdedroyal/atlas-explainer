"""Untrusted baked assets must be checked without installing the authoring extras."""
import json

import pytest
import yaml

from atlas_explainer.pack import inline_media, lint_card, load_media, pack_card, pack_html


def card(tmp_path, kind="anim"):
    d = tmp_path / "demo"
    (d / "media").mkdir(parents=True)
    (d / "card.yaml").write_text(yaml.safe_dump({"kit": 1, "id": "demo", "title": "Demo",
        "questions": ["Why?"], "summary": "Media test.", "anchors": ["demo.py"]}), "utf-8")
    (d / "index.html").write_text(f'''<html><head><link rel="stylesheet" href="atlas-kit:1.css"></head>
        <body><ex-{kind} src="atlas-media:flow" source="illustrative" caption="Example"></ex-{kind}>
        <script src="atlas-kit:1.js"></script></body></html>''', "utf-8")
    return d


def anim(d, **changes):
    m = {"kind": "anim", "id": "flow", "sheet": "flow.webp", "width": 8, "height": 8,
         "columns": 1, "frames": 1, "fps": 4, "ms": 250, "captions": [], "sources": {}, **changes}
    (d / "media/flow.json").write_text(json.dumps(m), "utf-8")
    return m


@pytest.mark.parametrize("sheet", ["../../private.png", "/private.png", "C:/private.png", "..\\private.png", "flow.svg"])
def test_sheet_cannot_read_outside_media_or_load_svg(tmp_path, sheet):
    d = card(tmp_path)
    m = anim(d, sheet=sheet)
    assert lint_card(d)
    with pytest.raises(ValueError):
        inline_media(d, {"flow": m}, ["flow"])


def test_symlink_sheet_is_rejected(tmp_path):
    d = card(tmp_path)
    secret = tmp_path / "private.webp"
    secret.write_bytes(b"private")
    try:
        (d / "media/flow.webp").symlink_to(secret)
    except OSError:
        pytest.skip("symlinks unavailable")
    m = anim(d)
    assert any("leaves" in e for e in lint_card(d))
    with pytest.raises(ValueError, match="leaves"):
        inline_media(d, {"flow": m}, ["flow"])


def test_missing_sheet_and_malformed_fields_are_lint_errors(tmp_path):
    d = card(tmp_path)
    anim(d)
    assert any("missing" in e for e in lint_card(d))
    anim(d, frames=0)
    assert any("positive integer" in e for e in lint_card(d))
    anim(d, sources=[])
    assert any("sources" in e for e in lint_card(d))


@pytest.mark.parametrize("svg", [
    '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
    '<svg><image href="data:image/png,broken" onerror="alert(1)"/></svg>',
    '<svg><script>alert(1)</script></svg>',
    '<svg><foreignObject><div/></foreignObject></svg>',
    '<svg><animate attributeName="href" to="javascript:alert(1)"/></svg>',
    '<svg><a href="javascript:alert(1)"><text>go</text></a></svg>',
    '<svg><image href="https://example.test/a.png"/></svg>',
    '<svg><rect fill="url(https://example.test/a.svg)"/></svg>',
    '<svg><g style="background:url(https://example.test/a.png)"/></svg>',
    '<!DOCTYPE svg [<!ENTITY a "test">]><svg><text>&a;</text></svg>',
])
def test_active_svg_is_rejected_at_lint_and_pack(tmp_path, svg):
    d = card(tmp_path, "chart")
    m = {"kind": "chart", "id": "flow", "svg": {"light": svg, "dark": svg}, "sources": {}}
    (d / "media/flow.json").write_text(json.dumps(m), "utf-8")
    assert lint_card(d)
    with pytest.raises(ValueError):
        pack_card(d, tmp_path / "out")
    with pytest.raises(ValueError):
        pack_html((d / "index.html").read_text("utf-8"), {}, media={"flow": m})


def test_json_source_data_is_not_a_manifest(tmp_path):
    d = card(tmp_path, "chart")
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><text>ok</text></svg>'
    (d / "media/flow.json").write_text(json.dumps({"kind": "chart", "id": "flow",
        "svg": {"light": svg, "dark": svg}, "sources": {}}), "utf-8")
    (d / "media/data.json").write_text('[{"value": 7}]', "utf-8")
    # Unreferenced source JSON is allowed even if it is unrelated to a baked asset.
    (d / "media/other.json").write_text('{"kind":"domain-data"}', "utf-8")
    assert lint_card(d) == []
    assert list(load_media(d)[0]) == ["flow"]


@pytest.mark.parametrize("kind", ["anim", "chart"])
@pytest.mark.parametrize("source,expected", [("", "needs source"), ('source="real"', "needs origin")])
def test_media_provenance_is_required(tmp_path, kind, source, expected):
    d = card(tmp_path, kind)
    page = d / "index.html"
    page.write_text(page.read_text("utf-8").replace('source="illustrative"', source), "utf-8")
    assert any(expected in e for e in lint_card(d))
