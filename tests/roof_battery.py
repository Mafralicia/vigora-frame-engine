"""Bateria de casos-limite de telhado: Revit simulado -> normalizador -> motor, sem erros nem conflitos 3D.

Cada caso: casa com paredes no contorno, telhado(s) de referência direto no motor, e o mesmo telhado como o
Revit exportaria (esboço por telhado ou esboço único L/T/U, com bordas divididas, invertidas, tortas, no
nível de cima, paredes do template). Exige: mesmo resultado, 0 erros, 0 peças se penetrando.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from shapely.geometry import Polygon, box          # noqa: E402
from shapely.ops import unary_union                 # noqa: E402

from vigora_frame.builder import run                # noqa: E402
from vigora_frame.clash import find_clashes         # noqa: E402
from vigora_frame.model import Project              # noqa: E402
from vigora_frame.revit_bridge import revit_solids  # noqa: E402
from vigora_frame.revit_import import normalize     # noqa: E402

D = 140.0      # espessura do quadro externo (wood)


def walls_for(outline_poly, H=2700.0, windows=True):
    """Paredes externas no contorno (eixo a meia espessura para dentro), uma janela por parede longa."""
    ax = outline_poly.buffer(-D / 2, join_style=2)
    pts = [tuple(round(c, 1) for c in p) for p in list(ax.exterior.coords)[:-1]]
    walls = []
    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ops = []
        if windows and L > 2600:
            ops = [{"id": f"J{i}", "kind": "window", "offset": round(L / 2 - 500, 1), "width": 1000.0,
                    "height": 1000.0, "sill": 1100.0}]
        walls.append({"id": f"W{i}", "level": "L1", "start": list(a), "end": list(b), "height": H, "openings": ops})
    return walls


def project(case):
    """Projeto de referência a partir do caso."""
    parts = case["parts"]
    U = unary_union([box(*p["rect"]) for p in parts])
    walls = walls_for(U, H=case.get("H", 2700.0))
    roofs = []
    for i, p in enumerate(parts):
        x0, y0, x1, y1 = p["rect"]
        r = {"id": f"R{i + 1}", "level": "L1", "kind": p["kind"], "ridge_axis": p["axis"], "pitch_deg": case["pitch"],
             "outline": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}
        if p.get("ends"):
            r["ends"] = p["ends"]
        if p.get("high_side"):
            r["high_side"] = p["high_side"]
        if case.get("ovh") is not None:
            r["overhang"] = case["ovh"]
        roofs.append(r)
    return Project.model_validate({"id": "BAT", "name": case["name"], "system": "wood", "ruleset": "wood-br-v1",
                                   "levels": [{"id": "L1", "name": "T", "elevation": 0, "height": 2700}],
                                   "walls": walls, "roofs": roofs})


def cases(seed=7, n_random=60):
    rnd = random.Random(seed)
    out = []
    # 1) retângulos: todos os tipos, inclinações e beirais extremos
    for kind, axis, hs in (("gable", "x", None), ("gable", "y", None), ("hip", "x", None), ("hip", "y", None),
                           ("mono", "x", "end"), ("mono", "x", "start"), ("mono", "y", "end"), ("mono", "y", "start")):
        for pitch in (5, 15, 30, 45, 55):
            for ovh in (0.0, 300.0, 1000.0):
                W, Dp = rnd.choice([4800, 7200, 10800]), rnd.choice([3600, 6000, 8400])
                if kind == "mono":
                    if pitch > 30:
                        continue                              # meia-água íngreme: altura de transporte
                    sp_ = rnd.choice([3600, 4800])            # vão da meia-água dentro da tabela (máx. 7,0 m)
                    W, Dp = (W, sp_) if axis == "x" else (sp_, Dp)
                if kind == "hip":                             # cumeeira do 4 águas no lado longo da planta
                    W, Dp = (max(W, Dp), min(W, Dp)) if axis == "x" else (min(W, Dp), max(W, Dp))
                    if abs(W - Dp) < 1200:
                        continue
                if pitch >= 45 and max(W, Dp) > 7200:
                    continue
                sp_ = Dp if axis == "x" else W                # banzo superior até a barra de 6 m
                if ((sp_ if kind == "mono" else sp_ / 2) + ovh) / math.cos(math.radians(pitch)) > 5900:
                    continue
                out.append({"name": f"{kind}-{axis}-{hs or ''}-{pitch}-{ovh:.0f}", "pitch": pitch, "ovh": ovh,
                            "parts": [{"rect": (0, 0, W, Dp), "kind": kind, "axis": axis, "high_side": hs}]})
    # 2) L, T, U: asa(s) de 2 águas perpendiculares ao principal (rincão), em várias posições
    for _ in range(n_random):
        W, Dm = rnd.choice([9600, 10800, 12000]), rnd.choice([6000, 7200, 8400])
        ww, wd = rnd.choice([2400, 3600, 4800]), rnd.choice([1800, 3000, 4200])
        ww = min(ww, Dm - 1200)
        shape = rnd.choice(["L", "T", "U"])
        pitch = rnd.choice([20, 25, 30, 35, 40])
        ovh = rnd.choice([0.0, 400.0, 600.0])
        main_kind = rnd.choice(["gable", "gable", "hip"])
        if shape == "L":
            xs = [0.0]
        elif shape == "T":
            xs = [round((W - ww) / 2 / 100) * 100]
        else:
            xs = [0.0, W - ww]
            if W - 2 * ww < 1800:
                continue                                  # U sem pátio entre as asas: não é uma U
        if main_kind == "hip":
            xs = [max(x, Dm / 2 + 600) if x == 0 else min(x, W - Dm / 2 - 600 - ww) for x in xs]
            if len(xs) > 1 and xs[1] - xs[0] < ww + 600:
                continue
        parts = [{"rect": (0, 0, W, Dm), "kind": main_kind, "axis": "x"}]
        for x in xs:
            parts.append({"rect": (x, -wd, x + ww, 0), "kind": "gable", "axis": "y", "ends": ["gable", "valley"]})
        out.append({"name": f"{shape}-{main_kind}-W{W}-D{Dm}-w{ww}x{wd}-{pitch}-{ovh:.0f}", "pitch": pitch,
                    "ovh": ovh, "parts": parts})
    return out


def dirty(raw, rnd):
    """Sujeira de desenho do Revit: bordas divididas e invertidas, torta (<= 1°), paredes do template, nível de cima."""
    for r in raw["roofs"]:
        new = []
        for e in r["edges"]:
            if rnd.random() < 0.3:
                m = [(e["p0"][0] + e["p1"][0]) / 2, (e["p0"][1] + e["p1"][1]) / 2]
                new += [dict(e, p1=m), dict(e, p0=m)]
            else:
                new.append(e)
        for e in new:
            if rnd.random() < 0.3:
                e["p0"], e["p1"] = e["p1"], e["p0"]
        r["edges"] = new
    for w in raw["walls"]:
        w["type_function"], w["structural"] = "Exterior", False
    top = max(l["elevation"] for l in raw["levels"]) + 2700.0
    raw["levels"].append({"rid": 399, "name": "Cobertura", "elevation": top})
    for r in raw["roofs"]:
        r["level_rid"] = 399
    return raw


def summary(r):
    return (sorted((t.type, t.count, round(t.span)) for t in r.trusses), len(r.panels))


def check(case, rnd, sketch="parts"):
    from test_revit_import import fake_raw, union_roof_raw
    p = project(case)
    ref = run(p)
    probs = []
    errs = [f"{i.code} {i.message[:70]}" for i in ref.issues if i.severity == "error"]
    if errs:
        return [f"ref: {e}" for e in errs[:3]]
    cl = find_clashes(revit_solids(ref)["solids"])
    if cl:
        probs += [f"conflito ref: {c['a']} × {c['b']} ({c['depth']} mm)" for c in cl[:3]]
    raw = union_roof_raw(p) if sketch == "union" else fake_raw(p)
    raw = dirty(raw, rnd)
    proj, notes = normalize(raw, {"system": "wood"})
    nerr = [n["message"][:90] for n in notes if n["severity"] == "error"]
    if nerr:
        return probs + [f"import: {e}" for e in nerr[:3]]
    got = run(proj)
    errs = [f"{i.code} {i.message[:70]}" for i in got.issues if i.severity == "error"]
    probs += [f"revit: {e}" for e in errs[:3]]
    if summary(got) != summary(ref):
        probs.append(f"revit difere: {summary(got)[0][:3]} vs {summary(ref)[0][:3]}")
    cl = find_clashes(revit_solids(got)["solids"])
    probs += [f"conflito revit: {c['a']} × {c['b']} ({c['depth']} mm)" for c in cl[:3]]
    return probs


if __name__ == "__main__":
    rnd = random.Random(11)
    cs = cases()
    bad = 0
    for k, c in enumerate(cs):
        sketch = "union" if (len(c["parts"]) > 1 and k % 2 == 0) else "parts"
        try:
            pr = check(c, rnd, sketch)
        except Exception as ex:                               # nenhum caso pode quebrar o motor
            pr = [f"EXCEÇÃO {type(ex).__name__}: {ex}"]
        if pr:
            bad += 1
            print(f"FALHA {c['name']} [{sketch}]")
            for x in pr:
                print("    ", x)
    print(f"{len(cs)} casos, {bad} com problema")
