"""Entrepiso, parede curva, arco e pilar."""
from collections import Counter

import pytest

from vigora_frame.builder import load_project, run


@pytest.fixture(scope="module")
def sobrado(examples_dir):
    return run(load_project(examples_dir / "sobrado_wood.json"))


@pytest.fixture(scope="module")
def pav(examples_dir):
    return run(load_project(examples_dir / "pavilhao_curvo.json"))


def test_joists_on_grid_and_spacing(sobrado):
    js = sorted({round((m.x0 + m.x1) / 2) for m in sobrado.members if m.role in ("JOIST",)})
    assert all(x % 400 == 0 for x in js)
    xs = sorted({round((m.x0 + m.x1) / 2) for m in sobrado.members if m.role in ("JOIST", "TAIL_JOIST", "TRIMMER", "RIM_SIDE")})
    assert max(b - a for a, b in zip(xs, xs[1:])) <= 400


def test_stair_opening(sobrado):
    r = Counter(m.role for m in sobrado.members if m.group == "floor")
    assert r["TRIMMER"] == 2 and r["FLOOR_HEADER"] == 2 and r["TAIL_JOIST"] >= 4
    for m in sobrado.members:
        if m.role == "BRIDGING":
            cx, cy = (m.x0 + m.x1) / 2, (m.z0 + m.z1) / 2
            assert not (3030 < cx < 6700 and 3080 < cy < 4080)       # nada atravessa o vão da escada


def test_upper_walls_sit_on_lower_walls(sobrado):
    assert not any(i.code == "V-024" for i in sobrado.issues)


def test_curved_wall_facets(pav):
    facets = [p for p in pav.panels if "-C1F" in p.id]
    assert len(facets) == 7
    assert all(p.length <= 700 for p in facets)
    bevels = [m for m in pav.members if m.role == "STUD_END" and "chanfro" in m.note]
    assert len(bevels) == 16                    # 8 juntas em meia-esquadria (6 entre facetas + 2 nas retas) x 2


def test_arch_fillers_are_special_cnc(pav):
    af = [m for m in pav.members if m.role == "ARCH_FILLER"]
    assert len(af) == 2 and all(m.special and m.polygon for m in af)


def test_column_selected_by_load(pav):
    col = next(m for m in pav.members if m.role == "COLUMN")
    assert col.item == "PILAR-3x38x140"                                # 6 m² x 3,5 kPa = 21 kN


def test_examples_have_no_errors(examples_dir):
    for f in sorted(examples_dir.glob("*.json")):
        name = f.stem
        r = run(load_project(f))
        errs = [i for i in r.issues if i.severity == "error"]
        assert errs == [], (name, errs[:3])
