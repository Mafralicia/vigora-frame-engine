"""Propriedades para qualquer parede gerada aleatoriamente (seção 17.2)."""
from collections import Counter

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from vigora_frame.builder import run
from conftest import one_wall

BAD = {"V-006", "V-061", "V-062", "V-057", "V-058", "V-063", "V-064", "V-065", "V-002", "V-022"}


@st.composite
def wall_case(draw):
    system = draw(st.sampled_from(["wood", "steel"]))
    L = draw(st.integers(1500, 16000))
    exterior = draw(st.booleans())
    bearing = draw(st.booleans())
    ops, x = [], draw(st.integers(400, 1200))
    while True:
        w = draw(st.integers(500, 1600))
        kind = draw(st.sampled_from(["window", "door"]))
        if x + w + 700 > L:
            break
        if kind == "door":
            ops.append({"id": f"O{len(ops)}", "kind": "door", "offset": x, "width": w, "height": 2100})
        else:
            ops.append({"id": f"O{len(ops)}", "kind": "window", "offset": x, "width": w,
                        "height": draw(st.integers(500, 1300)), "sill": draw(st.integers(800, 1100))})
        x += w + draw(st.integers(450, 3000))
    return one_wall(system=system, length=L, openings=ops, exterior=exterior, bearing=bearing)


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(proj=wall_case())
def test_random_walls_are_buildable(proj):
    res = run(proj)
    bad = [i for i in res.issues if i.severity == "error" and i.code in BAD]
    assert bad == [], bad[:3]
    L = sum(p.length for p in res.panels)
    assert abs(L - 0 - (proj.walls[0].end[0] - proj.walls[0].start[0])) < 1e-6
    ids = [m.id for m in res.members]
    assert len(ids) == len(set(ids))                               # IDs únicos


@settings(max_examples=15, deadline=None)
@given(proj=wall_case())
def test_run_is_deterministic(proj):
    a, b = run(proj), run(proj)
    assert a.model_dump_json() == b.model_dump_json()
