"""Treliças (Anexo A6): geometria sem sobreposição, nós nos banzos, altura correta."""
import math

import pytest
from shapely.geometry import Polygon

from vigora_frame.config import Catalog
from vigora_frame.engine.roofs import truss_geometry

CAT = Catalog.load()


@pytest.mark.parametrize("kind,span", [("kingpost", 4500), ("fink", 7200), ("fink", 9000), ("howe", 11000),
                                       ("pratt", 11000), ("mono", 5000), ("gable", 7200)])
@pytest.mark.parametrize("pitch", [15, 25, 35])
def test_truss_members_do_not_overlap_and_connect(kind, span, pitch):
    parts, info = truss_geometry(kind, span, pitch, 500, "W-38x140", "W-38x140", "W-38x89", CAT, spacing_studs=400)
    polys = [p.poly for p in parts]
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            assert polys[i].intersection(polys[j]).area < 5.0, (parts[i].role, parts[j].role)
    chords = [p.poly for p in parts if "CHORD" in p.role]
    for p in parts:
        if p.role in ("WEB", "GABLE_STUD"):
            touching = sum(1 for c in chords if p.poly.distance(c) < 1.0)
            assert touching >= 2, p.role              # cada barra de alma toca os dois banzos
    rise = (span / 2 if kind != "mono" else span) * math.tan(math.radians(pitch))
    assert info["rise"] == pytest.approx(rise)


def test_long_bottom_chord_is_spliced_at_node():
    parts, _ = truss_geometry("fink", 9000, 25, 500, "W-38x140", "W-38x140", "W-38x89", CAT)
    bc = [p for p in parts if p.role == "BOTTOM_CHORD"]
    assert len(bc) >= 2 and all(p.cut_length <= 6000 for p in bc)
    heel = 0.5 * 140 * 140 / math.tan(math.radians(25))      # ponta chanfrada sob o banzo superior
    assert sum(p.poly.area for p in bc) == pytest.approx(9000 * 140 + 2 * heel, rel=1e-6)
