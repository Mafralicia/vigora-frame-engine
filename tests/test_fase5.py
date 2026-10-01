"""Fase 5 (pranchas confiáveis): escada, bloqueios padronizados, fixações e chanfros nas pranchas, fontes."""
import re

import pytest

from conftest import ROOT
from vigora_frame.builder import load_project, run
from vigora_frame.model import StairSpec


@pytest.fixture(scope="module")
def sobrado():
    return run(load_project(ROOT / "examples" / "sobrado_4aguas.json"))


def test_stair_geometry_and_checks(sobrado):
    st = sobrado.stats["stairs"][0]
    assert st["n"] == 17 and abs(st["h"] * st["n"] - st["H"]) < 0.5
    assert st["h"] <= 180 and 620 <= st["blondel"] <= 650
    assert st["throat"] >= 90
    assert st["head_min"] >= 2000                       # medido sobre a linha dos bocéis
    ms = [m for m in sobrado.members if m.group == "stair"]
    assert sum(m.role == "STRINGER" for m in ms) == 3 and sum(m.role == "TREAD" for m in ms) == 16
    assert not [i for i in sobrado.issues if i.code in ("V-082", "V-083", "V-085") and i.severity == "error"]


def test_stair_headroom_is_flagged_when_hole_is_short():
    p = load_project(ROOT / "examples" / "sobrado_4aguas.json")
    p.floors[0].holes = [[(3000, 6200), (4000, 6200), (4000, 8800), (3000, 8800)]]
    r = run(p)
    assert any(i.code == "V-083" for i in r.issues)


def test_stair_hitting_wall_is_flagged():
    p = load_project(ROOT / "examples" / "sobrado_4aguas.json")
    p.stairs = [StairSpec(id="E1", level="L2", start=(2700, 4320), direction="+y", width=960)]
    r = run(p)
    assert any(i.code == "V-085" for i in r.issues)


def test_stair_solids_exist(sobrado):
    from vigora_frame.revit_bridge import revit_solids
    sol = [s for s in revit_solids(sobrado)["solids"] if s["group"] == "stair"]
    assert len(sol) == 19


def test_blocking_rows_are_standard():
    for n in ("casa_terrea_wood", "salao_de_festas", "casa_4aguas_steel"):
        r = run(load_project(ROOT / "examples" / f"{n}.json"))
        rows = {round((m.z0 + m.z1) / 2) for m in r.members if m.role == "BLOCK"}
        assert rows <= {1200, 2400} or all(v in (1200, 2400) or any(abs(v - q) < 120 for q in (2400,)) for v in rows), n


def test_pranchas_have_text_stair_fixings_and_bevels(tmp_path):
    import pypdfium2 as pdfium
    from vigora_frame.cli import export_all
    s = export_all(str(ROOT / "examples" / "salao_de_festas.json"), str(tmp_path / "sf"))
    pdf = pdfium.PdfDocument(str(tmp_path / "sf" / "pranchas_A1.pdf"))
    txt = "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
    assert "QUADRO DE FIXAÇÕES" in txt and "prego anelado" in txt
    assert re.search(r"CH 22\.5°", txt)
    assert "W-38x140" in txt                       # tabelas legíveis (fontes TrueType com Unicode)
    s2 = export_all(str(ROOT / "examples" / "sobrado_4aguas.json"), str(tmp_path / "sb"))
    pdf2 = pdfium.PdfDocument(str(tmp_path / "sb" / "pranchas_A1.pdf"))
    txt2 = "\n".join(pdf2[i].get_textpage().get_text_range() for i in range(len(pdf2)))
    assert "CORTE A-A" in txt2 and "linha dos bocéis" in txt2


def _text_overlaps(pdf_path, tol=0.3):
    import pypdfium2 as pdfium
    import pypdfium2.raw as raw
    pdf = pdfium.PdfDocument(pdf_path)
    total = 0
    for i in range(len(pdf)):
        bx = sorted(o.get_bounds() for o in pdf[i].get_objects(filter=[raw.FPDF_PAGEOBJ_TEXT]))
        bx = [b for b in bx if b[2] - b[0] > 0.2 and b[3] - b[1] > 0.2]
        for j, a in enumerate(bx):
            for b in bx[j + 1:]:
                if b[0] > a[2] - tol:
                    break
                if min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol:
                    total += 1
    return total


def test_no_text_overlaps_in_pranchas(tmp_path):
    from vigora_frame.cli import export_all
    for n in ("sobrado_4aguas", "salao_de_festas"):
        export_all(str(ROOT / "examples" / f"{n}.json"), str(tmp_path / n))
        assert _text_overlaps(str(tmp_path / n / "pranchas_A1.pdf")) == 0, n
