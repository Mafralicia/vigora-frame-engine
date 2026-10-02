"""Conflitos 3D entre todas as peças e bateria de casos-limite de telhado (Revit simulado)."""
import glob
import random

import pytest

from conftest import ROOT
from vigora_frame.builder import load_project, run
from vigora_frame.clash import find_clashes
from vigora_frame.revit_bridge import revit_solids

EXAMPLES = sorted(glob.glob(str(ROOT / "examples" / "*.json")))


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.split("/")[-1][:-5])
def test_no_part_penetrates_another(path):
    r = run(load_project(path))
    c = find_clashes(revit_solids(r)["solids"])
    assert not c, c[:3]


def test_detector_catches_planted_clash():
    r = run(load_project(ROOT / "examples" / "casa_terrea_wood.json"))
    sol = revit_solids(r)["solids"]
    stud = next(s for s in sol if s["role"] == "STUD")
    clone = dict(stud, id="PLANTADO", profile=[[p[0] + 10, p[1], p[2]] for p in stud["profile"]])
    found = find_clashes(sol + [clone])
    assert any("PLANTADO" in (c["a"], c["b"]) for c in found)


def test_touching_parts_are_not_clashes():
    r = run(load_project(ROOT / "examples" / "casa_terrea_wood.json"))
    sol = revit_solids(r)["solids"]
    stud = next(s for s in sol if s["role"] == "STUD")
    ex = stud["extrude"]
    clone = dict(stud, id="ENCOSTADO", profile=[[p[0] + ex[0], p[1] + ex[1], p[2]] for p in stud["profile"]])
    assert not any("ENCOSTADO" in (c["a"], c["b"]) for c in find_clashes(sol + [clone]))


def _battery_cases():
    import roof_battery as B
    cs = B.cases(seed=5, n_random=14)
    rnd = random.Random(5)
    picked = [c for c in cs if len(c["parts"]) == 1][::6] + [c for c in cs if len(c["parts"]) > 1]
    return [(c, "union" if k % 2 == 0 and len(c["parts"]) > 1 else "parts") for k, c in enumerate(picked)], rnd


_CASES, _RND = _battery_cases()


@pytest.mark.parametrize("case,sketch", _CASES, ids=[f"{c['name']}-{s}" for c, s in _CASES])
def test_roof_battery_revit_equals_engine_without_errors_or_clashes(case, sketch):
    import roof_battery as B
    assert B.check(case, _RND, sketch) == []
