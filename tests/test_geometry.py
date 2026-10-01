"""Geometria de curvas e arcos (Anexo A7) com os valores da especificação."""
import math

import pytest

from vigora_frame import geometry as g


def test_sagitta_values_from_spec():
    assert g.sagitta(5000, 600) == pytest.approx(9.0, abs=0.05)
    assert g.sagitta(3000, 400) == pytest.approx(6.7, abs=0.05)


def test_max_chord_for_sagitta():
    assert g.max_chord_for_sagitta(5000, 5) == pytest.approx(447, abs=1)


def test_arch_radius():
    assert g.arch_radius(1200, 300) == pytest.approx(750)
    assert g.arch_radius(1200, 600) == pytest.approx(600)   # semicírculo


@pytest.mark.parametrize("R,a0,a1,cmax,smax", [(3000, 90, 0, 1200, 25), (5000, 0, 180, 1200, 5), (1500, 0, 45, 600, 10)])
def test_facets_respect_limits(R, a0, a1, cmax, smax):
    segs = g.facet_arc((0, 0), R, a0, a1, cmax, smax)
    chords = [g.dist(a, b) for a, b in segs]
    assert max(chords) - min(chords) < 1e-6                      # facetas iguais
    assert max(chords) <= cmax + 1e-6
    assert g.sagitta(R, max(chords)) <= smax + 1e-6
    for a, b in segs:                                            # vértices sobre o arco
        assert g.dist(a, (0, 0)) == pytest.approx(R)
    assert segs[0][0] == pytest.approx((R * math.cos(math.radians(a0)), R * math.sin(math.radians(a0))))


def test_arch_fillers_close_the_rectangle():
    polys = g.arch_filler_polygons(1200, 600, 1800)
    from shapely.geometry import Polygon
    area = sum(Polygon(p).area for p in polys)
    # retângulo 1200 x 600 menos meio círculo de raio 600
    assert area == pytest.approx(1200 * 600 - math.pi * 600 ** 2 / 2, rel=0.01)
