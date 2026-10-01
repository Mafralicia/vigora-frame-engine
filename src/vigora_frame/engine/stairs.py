"""Escada reta de madeira: longarinas recortadas (dente de serra) e pisos.

Degraus pela regra de Blondel (2h + b entre 620 e 640 mm). Verificações: espelho, passo, garganta da
longarina, altura livre sob o piso de cima (2,00 m), chegada na borda do vão e interferência com paredes.
"""
from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon

from ..model import StairSpec
from .context import Ctx

BIG = 1e5
DIRS = {"+x": (1.0, 0.0), "-x": (-1.0, 0.0), "+y": (0.0, 1.0), "-y": (0.0, -1.0)}


def stair_geometry(H: float, st: StairSpec, cat) -> dict:
    n = math.ceil(H / st.riser_max - 1e-9)
    h = H / n
    b = st.tread or min(280.0, max(250.0, round(635 - 2 * h)))
    tt = cat.depth(st.tread_item) if cat.get(st.tread_item)["category"] != "sheet" else 25.0
    tt = cat.face(st.tread_item)                # piso deitado: espessura = face da peça
    D = cat.depth(st.stringer)
    run = (n - 1) * b
    # longarina: abaixo do dente de serra (face inferior dos pisos), acima da linha inferior, z >= 0
    saw = [(0.0, -BIG), (0.0, h - tt)]
    for i in range(1, n - 1):
        saw += [(i * b, i * h - tt), (i * b, (i + 1) * h - tt)]
    saw += [(run, (n - 1) * h - tt), (run, -BIG)]
    tan = h / b
    cos = b / math.hypot(b, h)
    c0 = h - tt - D / cos                           # linha inferior: z = u*tan + c0 (paralela aos cantos externos)
    below = Polygon([(-BIG, -BIG * tan + c0), (BIG, BIG * tan + c0), (BIG, BIG), (-BIG, BIG)])
    stringer = Polygon(saw).intersection(below).intersection(Polygon([(-1, 0), (run + 1, 0), (run + 1, BIG), (-1, BIG)]))
    # garganta: menor distância dos cantos internos à linha inferior
    inner = [(i * b, i * h - tt) for i in range(1, n - 1)]
    line = LineString([(-BIG, -BIG * tan + c0), (BIG, BIG * tan + c0)])
    throat = min((line.distance(Point(p)) for p in inner), default=D)
    return {"n": n, "h": h, "b": b, "tt": tt, "run": run, "D": D, "blondel": 2 * h + b, "throat": throat,
            "stringer": stringer, "pitch": math.degrees(math.atan(tan)), "nosing": cat.depth(st.tread_item) - b}


def frame_stair(st: StairSpec, ctx: Ctx, levels: list, floors: list) -> None:
    ids = [l.id for l in levels]
    if st.level not in ids or ids.index(st.level) == 0:
        ctx.issue("V-082", "error", st.id, "escada sem pavimento de baixo")
        return
    up, low = levels[ids.index(st.level)], levels[ids.index(st.level) - 1]
    H = up.elevation - low.elevation
    sid = f"{ctx.pfx}-{st.level}-{st.id}"
    g = stair_geometry(H, st, ctx.cat)
    d = DIRS[st.direction]
    ac = (-d[1], d[0])                               # lado esquerdo de quem sobe
    left0 = (st.start[0] - ac[0] * st.width / 2, st.start[1] - ac[1] * st.width / 2)
    if g["h"] > 190:
        ctx.issue("V-082", "error", sid, f"espelho de {g['h']:.0f} mm (máx. 190)")
    if not 620 <= g["blondel"] <= 650:
        ctx.issue("V-082", "warning", sid, f"regra de Blondel 2h+b = {g['blondel']:.0f} mm (faixa 620–650)")
    if g["throat"] < 90:
        ctx.issue("V-082", "error", sid, f"garganta da longarina de {g['throat']:.0f} mm (mín. 90): use peça mais alta")
    if g["nosing"] < 0:
        ctx.issue("V-082", "error", sid, "peça do piso mais estreita que o passo")
    # peças
    face = ctx.cat.face(st.stringer)
    ns = 2 if st.width <= 900 else 3
    offs = [0.0, st.width - face] if ns == 2 else [0.0, (st.width - face) / 2, st.width - face]
    coords = [(round(x, 2), round(z, 2)) for x, z in st_coords(g["stringer"])]
    blank = math.hypot(g["run"], H) - (H - g["h"] + g["tt"]) * 0 + 50
    for k, off in enumerate(offs, 1):
        m = ctx.new_member("STRINGER", st.stringer, st.level, "stair", sid, frame="stair",
                           x0=min(c[0] for c in coords), x1=max(c[0] for c in coords), z0=0.0,
                           z1=max(c[1] for c in coords), orientation="A", polygon=coords,
                           cut_length=round(math.hypot(g["run"], (g["n"] - 1) * g["h"]) + g["D"] * 0.6, 1),
                           angle_a=round(90 - g["pitch"], 1), angle_b=round(g["pitch"], 1), special=True,
                           rule="stairs.stringer", note=f"longarina {k}/{ns}: recorte CNC de {g['n'] - 1} dentes")
        m.id = f"{sid}-STRINGER-{k:02d}"
        ctx.members.append(m)
        ctx.placements[m.id] = {"origin": (left0[0], left0[1], low.elevation), "span_dir": d, "off": off,
                                "thick": face}
    tw = ctx.cat.depth(st.tread_item)
    for i in range(1, g["n"]):
        u1 = i * g["b"]
        u0 = u1 - tw                                  # bocel para o lado de quem desce
        coords_t = [(u0, i * g["h"] - g["tt"]), (u1, i * g["h"] - g["tt"]), (u1, i * g["h"]), (u0, i * g["h"])]
        m = ctx.new_member("TREAD", st.tread_item, st.level, "stair", sid, frame="stair", x0=u0, x1=u1,
                           z0=i * g["h"] - g["tt"], z1=i * g["h"], orientation="H",
                           polygon=[(round(a, 2), round(b_, 2)) for a, b_ in coords_t],
                           cut_length=round(st.width, 1), rule="stairs.tread", note=f"degrau {i}")
        m.id = f"{sid}-TREAD-{i:02d}"
        ctx.members.append(m)
        ctx.placements[m.id] = {"origin": (left0[0], left0[1], low.elevation), "span_dir": d, "off": 0.0,
                                "thick": st.width}
    ctx.hw("PREGO-ANEL-3.3x90", 4 * ns * (g["n"] - 1), f"{sid} pisos nas longarinas (2 por apoio, cola PU)")
    ctx.hw("SUPORTE-VIGA-SV1", ns, f"{sid} longarinas na viga de borda do vão")
    ctx.hw("CHUMBADOR-M12", ns, f"{sid} pé das longarinas no piso de baixo (cantoneira)")

    # verificações em planta
    def P(u, v):
        return (left0[0] + d[0] * u + ac[0] * v, left0[1] + d[1] * u + ac[1] * v)
    fl = next((f for f in floors if f.level == st.level), None)
    head_min = None
    if fl is not None:
        fid = f"{ctx.pfx}-{fl.level}-{fl.id}"
        zb = ctx.placements.get(fid, {}).get("z", up.elevation) - low.elevation
        slab = Polygon(fl.outline)
        for hole in fl.holes:
            slab = slab.difference(Polygon(hole))
        u = 0.0
        while u <= g["run"] + 1:
            ztop = g["h"] + u * g["h"] / g["b"]          # linha dos bocéis (quinas dos degraus)
            for v in (5.0, st.width - 5.0):
                if slab.contains(Point(P(u, v))):
                    cl = zb - ztop
                    head_min = cl if head_min is None else min(head_min, cl)
            u += 25.0
        if head_min is not None and head_min < 2000:
            ctx.issue("V-083", "error", sid, f"altura livre de {head_min:.0f} mm sobre a linha dos bocéis (mín. 2000): "
                                             "aumente o vão da escada no sentido da subida")
        top = Point(P(g["run"], st.width / 2))
        if min(Polygon(hh).exterior.distance(top) for hh in fl.holes) > 30 if fl.holes else True:
            ctx.issue("V-084", "warning", sid, "a escada não chega na borda do vão do piso")
    else:
        ctx.issue("V-084", "warning", sid, "escada sem piso de chegada definido")
    foot = Polygon([P(0, 0), P(g["run"], 0), P(g["run"], st.width), P(0, st.width)])
    for wf in ctx.wall_frames.values():
        if wf.wall.level != low.id:
            continue
        nrm = (-wf.dirv[1] * wf.depth / 2, wf.dirv[0] * wf.depth / 2)
        a, b_ = wf.origin, wf.to_global(wf.L)
        band = Polygon([(a[0] + nrm[0], a[1] + nrm[1]), (b_[0] + nrm[0], b_[1] + nrm[1]),
                        (b_[0] - nrm[0], b_[1] - nrm[1]), (a[0] - nrm[0], a[1] - nrm[1])])
        if band.intersection(foot).area > 1:
            ctx.issue("V-085", "error", sid, f"escada bate na parede {wf.wall.id}")
    ctx.stairs.append({"id": sid, "level": st.level, "low": low.id, "H": H, "n": g["n"], "h": g["h"], "b": g["b"],
                       "run": g["run"], "width": st.width, "blondel": g["blondel"], "throat": g["throat"],
                       "pitch": g["pitch"], "left0": left0, "dir": d, "across": ac, "head_min": head_min,
                       "tt": g["tt"], "nosing": g["nosing"], "stringers": ns, "floor_bottom":
                       (ctx.placements.get(f"{ctx.pfx}-{fl.level}-{fl.id}", {}).get("z") if fl else None)})


def st_coords(poly):
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area)
    return list(poly.exterior.coords)[:-1]
