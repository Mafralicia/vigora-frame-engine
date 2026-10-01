"""Caixa d'água no ático (padrão Vigora): posição, apoio desacoplado, treliças de ático, colisão, operações."""
import json
import math

import pytest

from conftest import ROOT
from vigora_frame.builder import load_project, run


def proj(**kw):
    p = load_project(ROOT / "examples" / "casa_caixa_dagua.json")
    for k, v in kw.items():
        setattr(p.tanks[0], k, v)
    return p


@pytest.fixture(scope="module")
def base():
    return run(proj())


def test_auto_position_at_bearing_wall_intersection(base):
    t = base.stats["tanks"][0]
    assert t["center"] == [4200.0, 4200.0] and t["how"] == "auto-A"
    assert set(t["supports"]) == {"H1", "H2"} and t["span_beam"] <= 1500
    assert not [i for i in base.issues if i.severity == "error"]


def test_support_is_decoupled_from_trusses(base):
    beams = [m for m in base.members if m.role == "TANK_BEAM"]
    assert len(beams) >= 4 and all(m.item == "W-38x235" and m.plies == 2 for m in beams)
    planes = sorted({round(v["origin"][0]) for k, v in base.stats["placements"].items() if "-R1-TR" in k})
    for m in beams:                                  # nenhuma viga sob banzo de treliça (>= 60 mm livres)
        for pl in planes:
            assert m.x1 <= pl - 19 - 60 + 0.5 or m.x0 >= pl + 19 + 60 - 0.5


def test_trusses_crossing_envelope_become_attic_trusses(base):
    t = base.stats["tanks"][0]
    attic = {m.parent for m in base.members if m.frame == "truss" and "marca A" in m.note}
    assert len(attic) == 3
    for tid in attic:
        o = base.stats["placements"][tid]["origin"]
        d = max(abs(o[0] - t["center"][0]) - 38, 0)
        w = math.sqrt(t["R_tray"] ** 2 - d ** 2)
        cs = t["center"][1] - o[1]
        from shapely.geometry import Polygon, box
        env = box(cs - w, t["deck_top"] - o[2], cs + w, t["env_top"] - o[2])
        for m in base.members:
            if m.parent == tid:
                assert Polygon(m.polygon).intersection(env).area < 1.0, m.id


def test_no_clash_and_purchase_items(base):
    assert any(i.code == "V-000" and "sem colisão" in i.message for i in base.issues)
    items = {h.item for h in base.hardware}
    assert {"CAIXA-BR_1000L", "BACIA-CONTENCAO-1700", "TUBO-PVC-32"} <= items


def test_swap_move_remove_regenerate_surroundings(base):
    r5 = run(proj(model="BR_500L"))
    assert r5.stats["tanks"][0]["model"] == "BR_500L" and not [i for i in r5.issues if i.severity == "error"]
    rm = run(proj(position=(7000, 4200)))
    planes = sorted(round(v["origin"][0]) for k, v in rm.stats["placements"].items()
                    if any(m.parent == k and "marca A" in m.note for m in rm.members))
    assert planes and all(abs(p_ - 7000) < 900 for p_ in planes)
    p = load_project(ROOT / "examples" / "casa_caixa_dagua.json")
    p.tanks = []
    r0 = run(p)
    assert not any("marca A" in m.note for m in r0.members) and not any(m.role == "TANK_BEAM" for m in r0.members)


def test_errors_bad_position_low_roof_unknown_model():
    assert any(i.code == "V-091" for i in run(proj(position=(4200, 1500))).issues)
    p = proj()
    p.roofs[0].pitch_deg = 22
    r = run(p)
    assert any(i.code == "V-090" for i in r.issues) and any(i.code == "V-093" for i in r.issues)
    assert any(i.code == "V-094" for i in run(proj(model="BR_2000L")).issues)


def test_cli_commands(tmp_path):
    import subprocess
    import sys
    f = tmp_path / "cx.json"
    f.write_text((ROOT / "examples" / "casa_caixa_dagua.json").read_text(encoding="utf-8"), encoding="utf-8")
    env = {"PYTHONPATH": str(ROOT / "src")}
    for args in (["trocar", str(f), "BR_500L"], ["mover", str(f), "--x", "7000", "--y", "4200"], ["remover", str(f)],
                 ["adicionar", str(f), "--modelo", "BR_1000L"]):
        out = subprocess.run([sys.executable, "-m", "vigora_frame.cli", "caixa", *args], capture_output=True, text=True,
                             env=env, cwd=ROOT)
        assert out.returncode == 0, out.stdout + out.stderr
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["tanks"] == [{"id": "CX1", "model": "BR_1000L", "level": "L1"}]
