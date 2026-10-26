from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from atlas_explainer.cli import main
from atlas_explainer.pack import CSP, lint_card, pack_card

EXAMPLES = Path(__file__).parent.parent / "examples"
GOOD = EXAMPLES / "order-cleaning-pipeline"


@pytest.fixture
def card(tmp_path) -> Path:
    dst = tmp_path / "order-cleaning-pipeline"
    shutil.copytree(GOOD, dst)
    return dst


def edit(card: Path, old: str, new: str, file: str = "index.html"):
    p = card / file
    text = p.read_text("utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new, 1), "utf-8")


def test_example_is_clean(card):
    assert lint_card(card) == []


def test_pack_inlines_kit_and_adds_csp(card, tmp_path):
    meta = pack_card(card, tmp_path / "out")
    html = (tmp_path / "out" / "index.html").read_text("utf-8")
    assert "atlas-kit:" not in html
    assert CSP in html
    assert "atlas:height" in html and "--ex-accent" in html
    assert '<html lang="zh">' in html
    assert meta["id"] == "order-cleaning-pipeline"


@pytest.mark.parametrize("old,new,needle", [
    ('<ex-table source="illustrative"', "<ex-table", "needs source"),
    ('<ex-table source="illustrative"', '<ex-table source="real"', "needs origin"),
    ("</body>", '<script>fetch("https://x.test")</script></body>', "custom scripts"),
    ("<p>每行是一笔订单", '<img src="https://example.com/a.png"><p>每行是一笔订单', "points outside"),
    ("<p>每行是一笔订单", '<a href="https://example.com">x</a><p>每行是一笔订单', "points outside"),
    ("<p>每行是一笔订单", '<iframe src="#x"></iframe><p>每行是一笔订单', "not allowed"),
    ("<p>每行是一笔订单", '<p onclick="1">每行是一笔订单', "event handler"),
    ("<p>每行是一笔订单", '<p style="background:url(https://x.test/a.png)">每行是一笔订单', "external resource"),
    ('<link rel="stylesheet" href="atlas-kit:1.css">', "", "missing `<link"),
    ('<ex-stage title="补全空品类"', "<ex-stage", "needs a title"),
])
def test_lint_rejects(card, old, new, needle):
    edit(card, old, new)
    problems = lint_card(card)
    assert any(needle in p for p in problems), problems


def test_lint_rejects_compare_without_sides(card):
    edit(card, "<ex-before>", "<div>")
    edit(card, "</ex-before>", "</div>")
    assert any("<ex-before>" in p for p in lint_card(card))


def test_lint_rejects_empty_flow(card):
    html = (card / "index.html").read_text("utf-8")
    start, end = html.index("<ex-flow>"), html.index("</ex-flow>")
    (card / "index.html").write_text(html[:start] + "<ex-flow></ex-flow>" + html[end + len("</ex-flow>"):], "utf-8")
    assert any("no <ex-stage>" in p for p in lint_card(card))


def test_allowed_links_pass(card):
    edit(card, "<p>每行是一笔订单", '<p><a href="#top">top</a> <a href="atlas://a.py#f">f</a> '
                                     '<img src="data:image/png;base64,AAAA"></p><p>每行是一笔订单')
    assert lint_card(card) == []


@pytest.mark.parametrize("old,new,needle", [
    ("kit: 1", "kit: 2", "kit"),
    ("id: order-cleaning-pipeline", "id: Bad_Id", "id"),
    ("id: order-cleaning-pipeline", "id: other-name", "must equal the directory name"),
    ("  - pipeline/clean.py\n  - pipeline/normalize.py#canon_label\n", "  []\n", "anchors"),
    ("questions:\n  - 订单表里到底存了什么？\n  - 为什么要先修空品类、再删体系外的行？\n  - 清洗之后的品类标签长什么样？\n", "", "questions"),
    ("tags: [example]", "tags: [no spaces allowed]", "tags"),
])
def test_manifest_rejects(card, old, new, needle):
    text = (card / "card.yaml").read_text("utf-8")
    if "anchors" in needle:
        text = text.replace("anchors:\n" + old, "anchors: " + new.strip() + "\n")
    else:
        assert old in text, old
        text = text.replace(old, new, 1)
    (card / "card.yaml").write_text(text, "utf-8")
    assert any(needle in p for p in lint_card(card)), lint_card(card)


def test_size_limit(card):
    edit(card, "<p>每行是一笔订单", "<!--" + "x" * 210_000 + "--><p>每行是一笔订单")
    assert any("limit" in p for p in lint_card(card))


def test_cli_pack_writes_index(card, tmp_path, capsys):
    out = tmp_path / "cards"
    assert main(["pack", str(card), "-o", str(out)]) == 0
    assert json.loads((out / "index.json").read_text("utf-8"))[0]["id"] == "order-cleaning-pipeline"
    assert (out / "order-cleaning-pipeline" / "index.html").exists()


def test_cli_lint_fails_on_bad_card(card, capsys):
    edit(card, "kit: 1", "kit: 9", "card.yaml")
    assert main(["lint", str(card)]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
