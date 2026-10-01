"""Quantitativo e otimização de corte (seção 10)."""
import random

from hypothesis import given, settings
from hypothesis import strategies as st

from vigora_frame.builder import load_project, run
from vigora_frame.config import Catalog, Rules
from vigora_frame.quantities import lower_bound, optimize_cuts, quantities


@settings(max_examples=80, deadline=None)
@given(pieces=st.lists(st.floats(80, 6000), min_size=1, max_size=120))
def test_cut_optimizer_properties(pieces):
    ps = [(f"p{i}", round(L, 1)) for i, L in enumerate(pieces)]
    bars, too_long = optimize_cuts(ps, [3000, 3600, 4800, 6000], kerf=3)
    assert not too_long
    allocated = sorted(c for b in bars for c in b.cuts)
    assert allocated == sorted(ps)                                  # toda peça em uma barra, uma vez
    for b in bars:
        assert b.used(3) <= b.stock + 1e-6
    lb = lower_bound(ps, 6000, 3)
    assert lb <= len(bars) <= max(lb * 1.25 + 1, lb + 2)            # perto do limite teórico


def test_too_long_piece_is_flagged():
    _, too_long = optimize_cuts([("a", 7000)], [6000], 3)
    assert too_long == [("a", 7000)]


def test_house_quantities_are_consistent(examples_dir):
    r = run(load_project(examples_dir / "casa_terrea_wood.json"))
    q = quantities(r, Catalog.load(), Rules.load("wood-br-v1"))
    cut = sum(m.cut_length * m.plies for m in r.members if not m.special) / 1000
    assert abs(q["summary"]["linear_m"] - cut) < 0.5
    assert 0.85 < q["summary"]["yield"] <= 1.0
    assert q["summary"]["sheets"] >= 20
