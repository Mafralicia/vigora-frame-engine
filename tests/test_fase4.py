"""Fase 4: sem vãos entre peças, junções (X, meia-esquadria), telhados 4 águas/encostado/meia-água, pranchas NBR."""
import math

import pytest
from shapely.geometry import Polygon

from conftest import ROOT
from vigora_frame.builder import load_project, run
from vigora_frame.model import Project
from vigora_frame.revit_bridge import revit_solids


def _box(extra_walls, system="wood"):
    walls = [{"id": "A", "level": "L1", "start": [0, 0], "end": [6000, 0], "height": 2700},
             {"id": "C", "level": "L1", "start": [0, 0], "end": [0, 4000], "height": 2700},
             {"id": "N", "level": "L1", "start": [0, 4000], "end": [6000, 4000], "height": 2700},
             {"id": "E", "level": "L1", "start": [6000, 0], "end": [6000, 4000], "height": 2700}] + extra_walls
    return Project.model_validate({"id": "T", "name": "t", "system": system,
                                   "ruleset": "wood-br-v1" if system == "wood" else "steel-br-v1",
                                   "levels": [{"id": "L1", "name": "T", "elevation": 0, "height": 2700}],
                                   "walls": walls})


@pytest.fixture(scope="module")
def results():
    names = ["casa_4aguas_wood", "casa_4aguas_steel", "salao_de_festas", "sobrado_4aguas", "casa_em_L_dois_telhados",
             "casa_meia_agua_steel_invertida", "pavilhao_curvo"]
    return {n: run(load_project(ROOT / "examples" / f"{n}.json")) for n in names}


def test_no_random_gaps_anywhere(results):
    for n, r in results.items():
        assert not [i for i in r.issues if i.code in ("V-074", "V-075", "V-076")], n


def test_gap_between_studs_is_never_between_2_5_and_60(results):
    for n, r in results.items():
        by = {}
        for m in r.members:
            if m.frame == "panel" and m.plane == "core" and m.orientation == "V":
                by.setdefault(m.parent, []).append(m)
        for pid, ms in by.items():
            for a in ms:
                for b in ms:
                    if a is b or not (a.z0 < b.z1 - 1 and b.z0 < a.z1 - 1):
                        continue
                    g = b.x0 - a.x1
                    if 2.5 < g < 60:
                        between = [c for c in ms if c.x0 < b.x0 - 0.5 and c.x1 > a.x1 + 0.5 and c.z0 < min(a.z1, b.z1)
                                   and c.z1 > max(a.z0, b.z0)]
                        assert between, (n, pid, a.id, b.id, g)


def test_wall_short_of_another_is_flagged():
    p = _box([{"id": "B", "level": "L1", "start": [3000, 120], "end": [3000, 3930], "height": 2700,
               "exterior": False, "bearing": False}])
    r = run(p)
    assert any(i.code == "V-075" and "sem encostar" in i.message for i in r.issues)


def test_x_crossing_is_split_into_two_tees():
    p = _box([{"id": "X1", "level": "L1", "start": [3000, 0], "end": [3000, 4000], "height": 2700, "exterior": False,
               "bearing": False},
              {"id": "X2", "level": "L1", "start": [0, 2000], "end": [6000, 2000], "height": 2700, "exterior": False,
               "bearing": True}])
    r = run(p)
    walls = {pn.wall for pn in r.panels}
    assert {"X1A", "X1B", "X2"} <= walls
    assert not [i for i in r.issues if i.severity == "error"]
    blocks = [m for m in r.members if m.role == "BACKER" and "-X2-" in m.id and "X1A+X1B" in m.note]
    assert len(blocks) == 4                             # um único bloco de 4 peças atende os dois lados


def test_miter_corner_has_no_overlap_in_3d(results):
    r = results["salao_de_festas"]
    sol = [s for s in revit_solids(r)["solids"] if s["group"] == "wall" and ("-K1-" in s["id"] or "-K2-" in s["id"])
           and s["role"] in ("STUD_END", "BOTTOM_PLATE")]
    polys = [(s["id"], Polygon([(p[0], p[1]) for p in s["profile"]])) for s in sol if s["extrude"][2] > 0]
    worst = max((a[1].intersection(b[1]).area for i, a in enumerate(polys) for b in polys[i + 1:]
                 if a[0].split("-K")[1][0] != b[0].split("-K")[1][0]), default=0)
    assert worst < 1.0
    posts = [m for m in r.members if m.role == "STUD_END" and "pilarete" in m.note]
    assert posts and all(m.special for m in posts)       # 135°: chanfro consome o montante -> pilarete CNC


def test_hip_roof_components(results):
    r = results["casa_4aguas_wood"]
    kinds = {t.mark[0] for t in r.trusses}
    assert {"T", "D", "M", "J"} <= kinds
    girder = [m for m in r.members if m.frame == "truss" and m.plies == 2]
    assert girder
    common_h = max(t.height for t in r.trusses if t.mark.startswith("T"))
    assert all(t.height <= common_h + 1 for t in r.trusses)
    assert len({m.id[:-1] for m in r.members if m.role == "HIP_RAFTER"}) == 4
    assert not [i for i in r.issues if i.code == "V-061"]


def test_hip_roof_steel_webs_do_not_overlap(results):
    r = results["casa_4aguas_steel"]
    assert not [i for i in r.issues if i.code == "V-061"]


def test_abut_roof_and_mono_high_side(results):
    r = results["casa_em_L_dois_telhados"]
    g = [t for t in r.trusses if t.mark.startswith("G")]
    assert sum(t.count for t in g) == 3                # 2 oitões no principal + 1 no anexo (a outra ponta encosta)
    r2 = results["casa_meia_agua_steel_invertida"]
    sd = {tuple(v["span_dir"]) for k, v in r2.stats["placements"].items() if "-TR" in k}
    assert sd == {(0, -1)}                             # lado alto no início: treliças viradas


def test_floor_sits_on_walls(results):
    r = results["sobrado_4aguas"]
    fl = [v for k, v in r.stats["placements"].items() if k.endswith("-F2")][0]
    assert abs(fl["z"] - 2700) <= 2.0


def test_pranchas_nbr_a1(tmp_path, results):
    from vigora_frame.config import Catalog, Rules
    from vigora_frame.export.pranchas_nbr import write_pranchas
    from vigora_frame.quantities import quantities
    r = results["sobrado_4aguas"]
    q = quantities(r, Catalog.load(), Rules.load(load_project(ROOT / "examples" / "sobrado_4aguas.json").ruleset))
    out = tmp_path / "p.pdf"
    n = write_pranchas(r, q, str(out), "A1")
    assert n >= 10 and out.stat().st_size > 50_000
    from pypdf import PdfReader
    pdf = PdfReader(str(out))
    assert len(pdf.pages) == n
    w, h = float(pdf.pages[0].mediabox.width), float(pdf.pages[0].mediabox.height)
    assert abs(w / 72 * 25.4 - 841) < 1 and abs(h / 72 * 25.4 - 594) < 1
