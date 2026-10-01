"""Painelização (seção 7.3)."""
from hypothesis import given, settings
from hypothesis import strategies as st

from vigora_frame.engine.walls import panelize


def test_short_wall_is_one_panel():
    assert panelize(5000, [], 6000, 600, 400)[0] == [(0.0, 5000)]


def test_joints_avoid_forbidden_and_prefer_grid():
    panels, ok = panelize(12000, [(5500, 6700)], 6000, 600, 400)
    assert ok
    joints = [b for _, b in panels[:-1]]
    assert all(not (5500 < j < 6700) for j in joints)
    assert all(j % 400 == 0 for j in joints)


@settings(max_examples=150, deadline=None)
@given(L=st.floats(700, 40000), zones=st.lists(st.tuples(st.floats(0, 40000), st.floats(200, 1800)), max_size=6))
def test_panelize_properties(L, zones):
    forb = [(a, a + w) for a, w in zones]
    panels, ok = panelize(L, forb, 6000, 600, 400)
    assert abs(sum(b - a for a, b in panels) - L) < 1e-6          # soma = comprimento
    assert panels[0][0] == 0 and abs(panels[-1][1] - L) < 1e-6
    if ok:
        assert all(b - a <= 6000 + 1e-6 for a, b in panels)
        assert len(panels) == 1 or all(b - a >= 600 - 1e-6 for a, b in panels)
        for _, j in panels[:-1]:
            assert all(not (a < j < b) for a, b in forb)
