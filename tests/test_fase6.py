"""Fase 2 de telhados: rincões (L/T/U, americano), parede alta, platibanda, alinhamento de beirais, complemento."""
import pytest

from conftest import ROOT
from vigora_frame.builder import load_project, run


@pytest.fixture(scope="module")
def R():
    names = ["casa_em_T_rincao", "casa_em_U_rincoes", "casa_americana_4aguas_rincao", "casa_meia_agua_parede_alta",
             "casa_platibanda", "casa_em_L_dois_telhados"]
    return {n: run(load_project(ROOT / "examples" / f"{n}.json")) for n in names}


def test_all_phase2_projects_have_no_errors(R):
    for n, r in R.items():
        assert not [i for i in r.issues if i.severity == "error"], n


def test_valley_trusses_sit_on_main_roof_plane(R):
    r = R["casa_em_T_rincao"]
    main = [v for k, v in r.stats["placements"].items() if k.startswith("CT11-L1-R1-TR")]
    info_z = main[0]["origin"][2]
    vs = [k for k, v in r.stats["placements"].items() if k.startswith("CT11-L1-R2-TR")
          and any(m.parent == k and "marca V" in m.note for m in r.members)]
    assert vs, "sem treliças de rincão"
    for k in vs:
        z = r.stats["placements"][k]["origin"][2]
        assert z > info_z + 200                              # apoiada sobre as águas, não sobre parede
    assert not any(i.code == "V-061" for i in r.issues)


def test_main_tails_cut_where_wing_attaches(R):
    r = R["casa_em_T_rincao"]
    trusses = {}
    for m in r.members:
        if m.parent.startswith("CT11-L1-R1-TR") and m.role == "TOP_CHORD":
            trusses.setdefault(m.parent, []).append(m)
    cut = [k for k, ms in trusses.items() if min(mm.x0 for mm in ms) > -1.0]
    full = [k for k, ms in trusses.items() if min(mm.x0 for mm in ms) < -100]
    assert cut and full                                       # na faixa da asa o beiral sul é cortado


def test_u_house_has_two_valley_sets_and_aligned_eaves(R):
    r = R["casa_em_U_rincoes"]
    assert sum(1 for t in r.trusses if t.mark.startswith("V")) >= 2
    assert not any(i.code == "V-087" for i in r.issues)
    assert len({t.mark for t in r.trusses}) == len(r.trusses)          # marcas únicas no projeto


def test_high_wall_mono_hangs_and_splits_tall_wall(R):
    r = R["casa_meia_agua_parede_alta"]
    assert any(p.level.startswith("L1C") for p in r.panels)           # painel de complemento
    assert any(h.item == "SUPORTE-VIGA-SV1" for h in r.hardware)
    assert any(m.role == "LEDGER" for m in r.members)
    assert all(p.height <= 3200 for p in r.panels)


def test_high_wall_too_low_is_flagged():
    p = load_project(ROOT / "examples" / "casa_meia_agua_parede_alta.json")
    for w in p.walls:
        if w.id == "N":
            w.height = 3300
    assert any(i.code == "V-086" for i in run(p).issues)


def test_parapet_roof_inside_walls(R):
    r = R["casa_platibanda"]
    pl = [v for k, v in r.stats["placements"].items() if "-R1-TR" in k]
    assert pl and all(abs(v["origin"][2] - 2700) < 0.5 for v in pl)
    ms = [m for m in r.members if m.group == "roof" and m.frame == "truss"]
    assert min(m.x0 for m in ms) >= -0.5                               # sem beiral
    assert any(i.code == "V-000" and "dois lados" in i.message for i in r.issues)


def test_eave_alignment_warning_and_fix():
    p = load_project(ROOT / "examples" / "casa_em_L_dois_telhados.json")
    p.roofs[1].overhang = 500
    r = run(p)
    w = [i for i in r.issues if i.code == "V-087"]
    assert w and "Para alinhar" in w[0].message
