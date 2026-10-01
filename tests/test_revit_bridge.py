"""Ponte Revit: sólidos 3D coerentes e lógica de atualização por diferença (API do Revit simulada)."""
import copy
import math
import sys
import types

import pytest

from vigora_frame.builder import load_project, run
from vigora_frame.revit_bridge import revit_solids
from conftest import ROOT

ACCESSORIES = {"BATTEN", "BC_RESTRAINT", "DIAG_BRACE"}


@pytest.fixture(scope="module")
def casa(examples_dir):
    r = run(load_project(examples_dir / "casa_terrea_wood.json"))
    return r, revit_solids(r)


def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def test_every_positioned_member_has_a_solid(casa):
    r, d = casa
    expected = [m for m in r.members if m.role not in ACCESSORIES]
    assert len(d["solids"]) == len(expected)


def test_profiles_are_planar_and_extrusion_is_normal(casa):
    _, d = casa
    for s in d["solids"]:
        p = s["profile"]
        n = None
        for i in range(1, len(p) - 1):
            c = _cross(_sub(p[i], p[0]), _sub(p[i + 1], p[0]))
            if math.hypot(*c) > 1e-3:
                n = c
                break
        assert n is not None, s["id"]
        L = math.hypot(*n)
        for q in p:                                      # todos os pontos no mesmo plano
            assert abs(sum(_sub(q, p[0])[k] * n[k] for k in range(3)) / L) < 0.5, s["id"]
        e = s["extrude"]
        el = math.hypot(*e)
        assert el > 0.5
        cos = abs(sum(e[k] * n[k] for k in range(3))) / (el * L)
        assert cos > 0.999, s["id"]                      # extrusão perpendicular ao perfil


def test_solids_inside_building_envelope(casa):
    _, d = casa
    xs = [p[0] for s in d["solids"] for p in s["profile"]]
    ys = [p[1] for s in d["solids"] for p in s["profile"]]
    zs = [p[2] for s in d["solids"] for p in s["profile"]]
    assert min(xs) >= -600 and max(xs) <= 8400 + 600
    assert min(ys) >= -600 and max(ys) <= 7200 + 600
    assert min(zs) >= -200 and max(zs) <= 2700 + 2100


def test_south_wall_studs_are_in_the_wall(casa):
    _, d = casa
    for s in d["solids"]:
        if "-W01-" in s["id"] and s["role"] == "STUD":
            ys = [p[1] for p in s["profile"]] + [s["profile"][0][1] + s["extrude"][1]]
            assert min(ys) >= -0.5 and max(ys) <= 140.5
            zs = [p[2] for p in s["profile"]]
            assert max(zs) - min(zs) == pytest.approx(s["cut_length"], abs=0.5)


# ------------------------------------------------------------ API do Revit simulada
class _Param:
    def __init__(self):
        self.v = ""

    def Set(self, v):
        self.v = v

    def AsString(self):
        return self.v


class _DS:
    registry = []
    _n = 0

    def __init__(self):
        _DS._n += 1
        self.Id = _DS._n
        self.ApplicationId = ""
        self.ApplicationDataId = ""
        self.Name = ""
        self.params = {"mark": _Param(), "com": _Param()}

    @classmethod
    def CreateElement(cls, doc, cat):
        d = cls()
        cls.registry.append(d)
        return d

    def SetShape(self, shape):
        self.shape = shape

    def get_Parameter(self, bip):
        return self.params[bip]


def _fake_db():
    DB = types.SimpleNamespace()
    DB.DirectShape = _DS
    DB.BuiltInParameter = types.SimpleNamespace(ALL_MODEL_MARK="mark", ALL_MODEL_INSTANCE_COMMENTS="com")
    DB.BuiltInCategory = types.SimpleNamespace(OST_GenericModel=1)
    DB.ElementId = lambda x: x

    class FEC:
        def __init__(self, doc):
            pass

        def OfClass(self, c):
            return list(_DS.registry)
    DB.FilteredElementCollector = FEC

    class T:
        def __init__(self, doc, name):
            pass

        def Start(self):
            pass

        def Commit(self):
            pass

        def RollBack(self):
            pass
    DB.Transaction = T
    return DB


class _Doc:
    def Delete(self, eid):
        _DS.registry = [d for d in _DS.registry if d.Id != eid]


def test_adapter_update_by_diff(casa, monkeypatch):
    DB = _fake_db()
    rev = types.ModuleType("Autodesk.Revit")
    rev.DB = DB
    monkeypatch.setitem(sys.modules, "Autodesk", types.ModuleType("Autodesk"))
    monkeypatch.setitem(sys.modules, "Autodesk.Revit", rev)
    sys.path.insert(0, str(ROOT / "adapters/revit_pyrevit/Vigora.extension/lib"))
    import importlib
    vr = importlib.import_module("vigora_revit")
    monkeypatch.setattr(vr, "_solido", lambda s: object())
    _DS.registry = []
    _, d = casa
    doc = _Doc()
    n = len(d["solids"])
    r1 = vr.aplicar_solidos(doc, d)
    assert r1 == {"criados": n, "mantidos": 0, "apagados": 0, "falhas": 0}
    r2 = vr.aplicar_solidos(doc, d)
    assert r2 == {"criados": 0, "mantidos": n, "apagados": 0, "falhas": 0}
    d2 = copy.deepcopy(d)
    d2["solids"][0]["sig"] = "alterada"
    removed = d2["solids"].pop()
    r3 = vr.aplicar_solidos(doc, d2)
    assert r3 == {"criados": 1, "mantidos": n - 2, "apagados": 2, "falhas": 0}
    assert len(_DS.registry) == n - 1
    assert all(ds.ApplicationDataId != removed["id"] for ds in _DS.registry)
