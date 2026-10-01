"""Importação do Revit: dados brutos (como o plugin extrai) -> projeto -> mesmo resultado dos exemplos."""
import copy
import json

import pytest

from conftest import ROOT
from vigora_frame.builder import load_project, run
from vigora_frame.revit_import import issues_for_revit, normalize


def fake_raw(p, rake=None, loc_line=0):
    """Simula a extração do plugin a partir de um projeto conhecido (ids numéricos como no Revit)."""
    lv_rid = {l.id: 300 + i for i, l in enumerate(p.levels)}
    raw = {"doc": {"title": p.name}, "levels": [{"rid": lv_rid[l.id], "name": l.name, "elevation": l.elevation}
                                                  for l in p.levels], "walls": [], "roofs": [], "floors": [],
           "stairs": [], "tanks": []}
    wrid = {}
    for i, w in enumerate(p.walls):
        rid = 10000 + i
        wrid[w.id] = rid
        width = 165.0
        (x0, y0), (x1, y1) = w.start, w.end
        L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        u = ((x1 - x0) / L, (y1 - y0) / L)
        ori = (u[1], -u[0])                                  # lado "externo" arbitrário (à direita)
        k = {0: 0.0, 2: -0.5}[loc_line]
        sh = (-ori[0] * k * width, -ori[1] * k * width)      # curva deslocada como o Revit guardaria
        raw["walls"].append({
            "rid": rid, "level_rid": lv_rid[w.level], "type_name": "PAREDE", "structural": w.bearing,
            "type_function": "Exterior" if w.exterior else "Interior", "width": width, "location_line": loc_line,
            "orientation": list(ori), "height": w.height,
            "curve": {"kind": "line", "p0": [x0 + sh[0], y0 + sh[1]], "p1": [x1 + sh[0], y1 + sh[1]]},
            "inserts": [{"rid": 50000 + i * 10 + j, "category": o.kind if o.kind == "door" else "window",
                         "center_along": o.offset + o.width / 2, "width": o.width, "height": o.height, "sill": o.sill}
                        for j, o in enumerate(w.openings)]})
    for i, r in enumerate(p.roofs):
        res = run(p)
        info = next(v for v in res.stats["roofs"] if v["id"].endswith("-" + r.id))
        o_al, Lr, o_sp, S, ov = info["o_along"], info["Lr"], info["o_span"], info["span"], info["ovh"]
        rk = ov if rake is None else rake
        e0 = rk if r.ends[0] == "gable" else 0.0
        e1 = rk if r.ends[1] == "gable" else 0.0
        if r.support == "parapet":
            d = 140.0
            a0, a1, s0, s1 = o_al + d, o_al + Lr - d, o_sp + d, o_sp + S - d
        else:
            a0, a1, s0, s1 = o_al - e0, o_al + Lr + e1, o_sp - ov, o_sp + S + ov
        if r.kind == "hip":
            a0, a1 = o_al - ov, o_al + Lr + ov
        g = (lambda al, sp: [al, sp]) if r.ridge_axis == "x" else (lambda al, sp: [sp, al])
        slope_lo = r.kind in ("gable", "hip") or r.high_side == "end"
        slope_hi = r.kind in ("gable", "hip") or r.high_side == "start"
        edges = [{"p0": g(a0, s0), "p1": g(a1, s0), "slope": slope_lo},
                 {"p0": g(a1, s0), "p1": g(a1, s1), "slope": r.kind == "hip"},
                 {"p0": g(a1, s1), "p1": g(a0, s1), "slope": slope_hi},
                 {"p0": g(a0, s1), "p1": g(a0, s0), "slope": r.kind == "hip"}]
        for e in edges:
            e["angle_deg"] = r.pitch_deg if e["slope"] else 0.0
        raw["roofs"].append({"rid": 70000 + i, "level_rid": lv_rid[r.level], "edges": edges,
                             "base_offset": r.bearing_height or 0.0})
    for i, f in enumerate(p.floors):
        raw["floors"].append({"rid": 80000 + i, "level_rid": lv_rid[f.level], "loops": [f.outline] + list(f.holes)})
    for i, s in enumerate(p.stairs):
        d = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}[s.direction]
        ids = [l.id for l in p.levels]
        raw["stairs"].append({"rid": 90000 + i, "base_level_rid": lv_rid[ids[ids.index(s.level) - 1]],
                              "top_level_rid": lv_rid[s.level],
                              "runs": [{"start": list(s.start), "end": [s.start[0] + d[0] * 4000, s.start[1] + d[1] * 4000],
                                        "width": s.width}]})
    for i, t in enumerate(p.tanks):
        raw["tanks"].append({"rid": 95000 + i, "level_rid": lv_rid[t.level], "model": t.model,
                             "point": list(t.position) if t.position else [0, 0], "auto": t.position is None})
    return raw


def summary(r):
    return (sorted((t.type, t.count, round(t.span)) for t in r.trusses), len(r.panels),
            r.stats["issues"].get("error", 0))


@pytest.mark.parametrize("name", ["casa_terrea_wood", "casa_4aguas_wood", "casa_em_T_rincao", "casa_em_U_rincoes",
                                  "casa_meia_agua_parede_alta", "casa_platibanda", "sobrado_4aguas",
                                  "casa_caixa_dagua", "casa_meia_agua_steel_invertida", "casa_em_L_dois_telhados",
                                  "casa_americana_4aguas_rincao", "salao_de_festas", "chale_40graus"])
def test_round_trip_matches_original(name):
    p = load_project(ROOT / "examples" / f"{name}.json")
    ref = run(p)
    raw = fake_raw(p)
    # escolhas que não dá para deduzir do desenho vêm da tela do telhado (configuração do plugin)
    cfg = {"system": p.system, "roofs": {str(rr["rid"]): {k: getattr(r, k) for k in ("girder_setback", "truss_type")
                                                          if getattr(r, k)}
                                         for rr, r in zip(raw["roofs"], p.roofs)}}
    proj, notes = normalize(raw, cfg)
    assert not [n for n in notes if n["severity"] == "error"], notes
    got = run(proj)
    assert summary(got) == summary(ref), name


def test_location_line_on_exterior_face_is_corrected():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    proj, _ = normalize(fake_raw(p, loc_line=2), {"system": "wood"})
    for a, b in zip(sorted(p.walls, key=lambda w: w.start), sorted(proj.walls, key=lambda w: w.start)):
        assert abs(a.start[0] - b.start[0]) < 0.2 and abs(a.start[1] - b.start[1]) < 0.2


def test_level_height_from_next_level():
    p = load_project(ROOT / "examples" / "sobrado_4aguas.json")
    proj, _ = normalize(fake_raw(p), {})
    assert abs(proj.levels[0].height - 2953.3) < 0.5


def test_user_choices_override_detection():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    raw = fake_raw(p)
    cfg = {"roofs": {str(raw["roofs"][0]["rid"]): {"truss_type": "howe", "spacing": 400}},
           "walls": {str(raw["walls"][0]["rid"]): {"bearing": False}}}
    proj, _ = normalize(raw, cfg)
    assert proj.roofs[0].truss_type == "howe" and proj.roofs[0].spacing == 400
    assert proj.walls[0].bearing is False


def test_bad_roof_and_errors_link_to_revit_elements():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    raw = fake_raw(p)
    raw["roofs"][0]["edges"][0]["p1"][1] += 300               # telhado girado/torto
    proj, notes = normalize(raw, {})
    assert any(n["code"] == "V-095" and n["rids"] == [raw["roofs"][0]["rid"]] for n in notes)
    raw2 = fake_raw(p)
    raw2["walls"][0]["curve"]["p1"][0] -= 250                 # parede que não encosta (longe demais p/ costurar)
    proj2, notes2 = normalize(raw2, {})
    iss = issues_for_revit(run(proj2), notes2)
    bad = [i for i in iss if i["code"] == "V-075"]
    assert bad and raw2["walls"][0]["rid"] in bad[0]["rids"] and bad[0]["hint"]


def test_split_roof_edges_are_merged():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    raw = fake_raw(p)
    e = raw["roofs"][0]["edges"][0]
    mid = [(e["p0"][0] + e["p1"][0]) / 2, (e["p0"][1] + e["p1"][1]) / 2]
    raw["roofs"][0]["edges"][0:1] = [dict(e, p1=mid), dict(e, p0=mid)]       # borda dividida em dois segmentos
    proj, notes = normalize(raw, {})
    assert not notes and proj.roofs[0].kind == "gable"


def revit_style_raw(p, width=180.0, loc_line=2):
    """Como o Revit guarda: curva na FACE EXTERNA (loc_line=2), pontas no cruzamento das linhas de localização
    nos cantos; parede em T termina na face da parede que ela encontra. Largura real (com acabamentos)."""
    raw = fake_raw(p)
    ext_ids = {w.id for w in p.walls if w.exterior}
    cx = sum(sum(c) for w in p.walls for c in (w.start, w.end)) / (4 * len(p.walls))
    for rw, w in zip(raw["walls"], p.walls):
        (x0, y0), (x1, y1) = w.start, w.end
        L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        u = ((x1 - x0) / L, (y1 - y0) / L)
        n = (-u[1], u[0])
        mid = ((x0 + x1) / 2, (y0 + y1) / 2)
        cy = sum(sum(c) for c in [q for ww in p.walls for q in (ww.start, ww.end)]) / 1
        # lado externo: o que se afasta do centro da casa
        c0 = (sum(q[0] for ww in p.walls for q in (ww.start, ww.end)) / (2 * len(p.walls)),
              sum(q[1] for ww in p.walls for q in (ww.start, ww.end)) / (2 * len(p.walls)))
        ori = n if (mid[0] - c0[0]) * n[0] + (mid[1] - c0[1]) * n[1] > 0 else (-n[0], -n[1])
        rw["orientation"] = list(ori)
        rw["width"] = width
        if w.id in ext_ids:
            rw["location_line"] = loc_line
            off = width / 2
            a = (x0 + ori[0] * off - u[0] * off, y0 + ori[1] * off - u[1] * off)   # vai até o canto externo
            b = (x1 + ori[0] * off + u[0] * off, y1 + ori[1] * off + u[1] * off)
        else:
            rw["location_line"] = 0
            a = (x0 + u[0] * width / 2, y0 + u[1] * width / 2)                     # para na face da outra
            b = (x1 - u[0] * width / 2, y1 - u[1] * width / 2)
        rw["curve"] = {"kind": "line", "p0": list(a), "p1": list(b)}
        for ins in rw["inserts"]:              # o Revit mede a partir do início da curva (que mudou)
            ins["center_along"] += (x0 - a[0]) * u[0] + (y0 - a[1]) * u[1]
    return raw


@pytest.mark.parametrize("name", ["casa_terrea_wood", "casa_4aguas_wood", "salao_de_festas"])
def test_revit_joined_walls_are_healed_to_axes(name):
    p = load_project(ROOT / "examples" / f"{name}.json")
    ref = run(p)
    proj, notes = normalize(revit_style_raw(p), {"system": p.system,
                                                 "roofs": {str(70000 + i): {k: getattr(r, k) for k in ("girder_setback",)
                                                                            if getattr(r, k)} for i, r in enumerate(p.roofs)}})
    got = run(proj)
    bad = [i for i in got.issues if i.code in ("V-075", "V-061", "V-069", "V-074")]
    assert not bad, [(i.code, i.message[:80]) for i in bad[:5]]
    assert summary(got) == summary(ref)


def test_drawing_gap_up_to_5mm_is_healed_and_logged_bigger_is_error():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    raw = fake_raw(p)
    raw["walls"][0]["curve"]["p1"][0] -= 4                    # 4 mm de folga: corrige e registra
    proj, notes = normalize(raw, {})
    assert not [i for i in run(proj).issues if i.code == "V-075"]
    assert any(n["code"] == "V-121" and raw["walls"][0]["rid"] in n["rids"] for n in notes)
    raw2 = fake_raw(p)
    raw2["walls"][0]["curve"]["p1"][0] -= 50                  # 50 mm: folga real de desenho -> erro, sem mexer
    proj2, notes2 = normalize(raw2, {})
    assert any(i.code == "V-075" for i in run(proj2).issues)


def test_degenerate_duplicate_and_zero_width_walls_are_ignored():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    raw = fake_raw(p)
    dup = json.loads(json.dumps(raw["walls"][1])); dup["rid"] = 77777
    zero = json.loads(json.dumps(raw["walls"][2])); zero["rid"] = 77778; zero["curve"]["p1"] = list(zero["curve"]["p0"])
    thin = json.loads(json.dumps(raw["walls"][3])); thin["rid"] = 77779; thin["width"] = 0.0
    raw["walls"] += [dup, zero, thin]
    proj, notes = normalize(raw, {})
    codes = {n["code"] for n in notes}
    assert {"V-128", "V-130", "V-131"} <= codes
    assert len(proj.walls) == len(p.walls)
    assert not [i for i in run(proj).issues if i.severity == "error"]


def test_project_truss_preference_only_where_span_fits():
    p = load_project(ROOT / "examples" / "casa_em_U_rincoes.json")
    raw = fake_raw(p)
    proj, _ = normalize(raw, {"roof_defaults": {"truss_type": "fink"}})
    r = run(proj)
    assert not [i for i in r.issues if i.code == "V-032"]          # asas de 3,6 m usam o tipo que cabe


def test_issue_lines_always_name_the_element():
    p = load_project(ROOT / "examples" / "casa_terrea_wood.json")
    raw = fake_raw(p)
    raw["walls"][0]["curve"]["p1"][0] -= 250
    proj, notes = normalize(raw, {})
    iss = issues_for_revit(run(proj), notes)
    assert all(i["message"].startswith("[") or not i["element"] or i["element"] in i["message"]
               for i in iss if i["severity"] == "error")
