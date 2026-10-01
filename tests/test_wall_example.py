"""Exemplo 7.5 da especificação: parede 6000 mm, montantes a 400, janela 1200 a 1500 mm."""
from collections import Counter

import pytest

from vigora_frame.builder import run
from conftest import errors, one_wall


@pytest.fixture(scope="module")
def res():
    return run(one_wall(openings=[{"id": "J1", "kind": "window", "offset": 1500, "width": 1200, "height": 1200,
                                   "sill": 1000}]))


def roles(res):
    return Counter(m.role for m in res.members if m.group == "wall")


def test_example_counts(res):
    r = roles(res)
    assert len(res.panels) == 1
    assert r["KING"] == 2 and r["JACK"] == 2 and r["HEADER"] == 1 and r["SILL"] == 1
    assert r["CRIPPLE"] == 6                                  # 3 acima da verga e 3 abaixo do peitoril
    assert r["STUD_END"] == 2
    studs = sorted(round((m.x0 + m.x1) / 2) for m in res.members if m.role == "STUD")
    # grade a 400; o montante de 2800 cai na zona do king e é substituído por um a meio caminho (2984)
    assert studs == [400, 800, 1200, 2984, 3200, 3600, 4000, 4400, 4800, 5200, 5600]
    full = sorted([19, 5981, 1433, 2767] + studs)
    gaps = [b - a for a, b in zip(full, full[1:]) if not (1433 <= a and b <= 2767)]
    assert max(gaps) <= 400
    cr = sorted({round((m.x0 + m.x1) / 2) for m in res.members if m.role == "CRIPPLE"})
    assert cr == [1600, 2000, 2400]


def test_example_header_and_lengths(res):
    h = next(m for m in res.members if m.role == "HEADER")
    # tabela pede 184; sobe para 235 porque o topo (2394) pararia 6 mm abaixo da junta da placa (2400)
    assert h.item == "W-38x235" and h.plies == 2 and "apoiar a junta" in h.note
    assert h.cut_length == pytest.approx(1220 + 2 * 38)      # vão estrutural + 1 jack de cada lado
    stud = next(m for m in res.members if m.role == "STUD")
    assert stud.cut_length == pytest.approx(2700 - 3 * 38)   # 1 placa inferior + 2 superiores
    jack = next(m for m in res.members if m.role == "JACK")
    assert jack.z1 == pytest.approx(1000 + 1200 + 10)        # até o topo do vão


def test_example_has_no_errors(res):
    assert errors(res) == []


def test_every_member_is_connected(res):
    deg = Counter()
    for c in res.connections:
        deg[c.a] += 1
        deg[c.b] += 1
    for m in res.members:
        if m.frame == "panel":
            assert deg[m.id] >= 2, m.id


def test_door_cuts_bottom_plate():
    r = run(one_wall(openings=[{"id": "P1", "kind": "door", "offset": 2000, "width": 900, "height": 2100}]))
    plates = sorted((m.x0, m.x1) for m in r.members if m.role == "BOTTOM_PLATE")
    assert len(plates) == 2
    assert plates[0][1] == pytest.approx(2000 - 10) and plates[1][0] == pytest.approx(2900 + 10)
    assert errors(r) == []


def test_opening_too_wide_is_reported():
    r = run(one_wall(length=9000, openings=[{"id": "J9", "kind": "window", "offset": 2000, "width": 4000,
                                             "height": 1200, "sill": 1000}]))
    assert any(i.code == "V-001" for i in r.issues)


def test_overlapping_openings_are_reported():
    r = run(one_wall(openings=[{"id": "A", "kind": "window", "offset": 1000, "width": 1000, "height": 1000, "sill": 1000},
                               {"id": "B", "kind": "window", "offset": 1900, "width": 800, "height": 1000, "sill": 1000}]))
    assert any(i.code == "V-022" for i in r.issues)
