"""Encontros entre paredes: canto (L), T, continuação e extremidade livre (seção 7.6).

Todas as paredes são dadas pelo eixo (linha de centro). O comprimento de framing
é o eixo mais as extensões de cada ponta:
  - canto L: a parede "passante" estende metade da espessura da outra;
             a parede "encostada" encurta metade da espessura da passante;
  - T: a parede que encosta encurta metade da espessura da parede contínua;
  - continuação (colinear ou faceta de curva): sem extensão.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .. import geometry as g
from ..model import Wall

TOL = 5.0


@dataclass
class EndInfo:
    kind: str = "free"            # free | through | butt | tee | inline | miter
    ext: float = 0.0              # extensão (+) ou encurtamento (-) na ponta
    other: str | None = None
    other_depth: float = 0.0      # profundidade da outra parede (para reforço de canto)
    clip: tuple | None = None     # meia-esquadria: reta (I, O) em planta que limita a parede
    bevel: float = 0.0            # diferença de comprimento entre face externa e interna (mm)
    miter_deg: float = 0.0        # ângulo do corte em relação ao esquadro


@dataclass
class WallJunctions:
    start: EndInfo = field(default_factory=EndInfo)
    end: EndInfo = field(default_factory=EndInfo)
    tees: list[tuple[float, float, str]] = field(default_factory=list)  # (t no eixo, profundidade, id)


def _priority(w: Wall, depth: float):
    L = g.dist(w.start, w.end)
    return (1 if w.exterior else 0, 1 if w.bearing else 0, round(L, 1), w.id)


def _faces(w: Wall, d: float):
    u = g.unit(g.sub(w.end, w.start))
    n = (-u[1], u[0])
    return [(g.add(w.start, g.mul(n, k * d / 2)), g.add(w.end, g.mul(n, k * d / 2))) for k in (1, -1)]


def _miter(info: EndInfo, w: Wall, end: str, P, o: Wall, oe: str, depth_of):
    """Meia-esquadria: as duas paredes terminam na reta que liga os cruzamentos das faces."""
    fw, fo = _faces(w, depth_of[w.id]), _faces(o, depth_of[o.id])
    pts = []
    for a in fw:
        best = None
        for b in fo:
            x = g.seg_intersection(a[0], a[1], b[0], b[1])
            if x is not None and (best is None or g.dist(x, P) < g.dist(best, P)):
                best = x
        pts.append(best)
    I, O = pts
    u = g.unit(g.sub(w.end, w.start))
    u_out = u if end == "end" else g.mul(u, -1)
    proj = [g.dot(g.sub(X, P), u_out) for X in (I, O)]
    info.kind = "miter"
    info.other = o.id
    info.ext = max(proj)                       # comprimento de framing até a ponta mais longa
    info.bevel = abs(proj[0] - proj[1])
    info.clip = (I, O)
    info.miter_deg = math.degrees(math.atan2(info.bevel, depth_of[w.id]))


def analyze(walls: list[Wall], depth_of: dict[str, float]) -> tuple[dict[str, WallJunctions], list[tuple]]:
    """Retorna o mapa de encontros e uma lista de problemas (código, parede, mensagem)."""
    res = {w.id: WallJunctions() for w in walls}
    problems = []
    by_level: dict[str, list[Wall]] = {}
    for w in walls:
        by_level.setdefault(w.level, []).append(w)

    for lvl, ws in by_level.items():
        for w in ws:
            for end in ("start", "end"):
                P = getattr(w, end)
                my_dir = g.unit(g.sub(w.end, w.start)) if end == "start" else g.unit(g.sub(w.start, w.end))
                info = getattr(res[w.id], end)
                is_tee = False
                # 1) ponta encostando no meio de outra parede (T)
                for o in ws:
                    if o.id == w.id:
                        continue
                    t, perp = g.project_param(P, o.start, o.end)
                    Lo = g.dist(o.start, o.end)
                    if perp <= TOL and TOL < t < Lo - TOL:
                        o_dir = g.unit(g.sub(o.end, o.start))
                        ang = g.angle_between_deg(my_dir, o_dir)
                        s = math.sin(math.radians(ang)) or 1.0
                        info.kind = "tee"
                        info.ext = -(depth_of[o.id] / 2) / s
                        info.other, info.other_depth = o.id, depth_of[o.id]
                        res[o.id].tees.append((t, depth_of[w.id] / s, w.id))
                        is_tee = True
                        break
                if is_tee:
                    continue
                # 2) outra parede com ponta no mesmo ponto
                cands = []
                for o in ws:
                    if o.id == w.id:
                        continue
                    for oe in ("start", "end"):
                        if g.dist(P, getattr(o, oe)) <= TOL:
                            cands.append((o, oe))
                if len(cands) > 1:
                    problems.append(("V-067", w.id, f"mais de duas paredes na ponta {end}; usando a primeira"))
                if cands:
                    o, oe = cands[0]
                    o_dir = g.unit(g.sub(o.end, o.start)) if oe == "start" else g.unit(g.sub(o.start, o.end))
                    ang = g.angle_between_deg(my_dir, o_dir)
                    if ang >= 179.0:  # continuação reta
                        info.kind, info.ext, info.other = "inline", 0.0, o.id
                        continue
                    if ang >= 120.0:  # meia-esquadria (faceta de curva, canto obtuso)
                        _miter(info, w, end, P, o, oe, depth_of)
                        continue
                    if abs(ang - 90.0) > 1.0:
                        problems.append(("V-078", w.id, f"encontro a {ang:.0f}° com {o.id}: use 90° ou entre 120° e 180°"))
                    s = math.sin(math.radians(ang)) or 1.0
                    if _priority(w, depth_of[w.id]) > _priority(o, depth_of[o.id]):
                        info.kind = "through"
                        info.ext = (depth_of[o.id] / 2) / s
                        info.other, info.other_depth = o.id, depth_of[o.id] / s
                    else:
                        info.kind = "butt"
                        info.ext = -(depth_of[o.id] / 2) / s
                        info.other, info.other_depth = o.id, depth_of[o.id]
                    continue
        # cruzamentos no meio das duas paredes (não suportado)
        for i, a in enumerate(ws):
            for b in ws[i + 1:]:
                p = g.seg_intersection(a.start, a.end, b.start, b.end)
                if p is None:
                    continue
                ta, pa = g.project_param(p, a.start, a.end)
                tb, pb = g.project_param(p, b.start, b.end)
                La, Lb = g.dist(a.start, a.end), g.dist(b.start, b.end)
                if TOL < ta < La - TOL and TOL < tb < Lb - TOL and pa < 1 and pb < 1:
                    problems.append(("V-068", a.id, f"parede cruza {b.id} no meio: divida uma das paredes no encontro"))
    return res, problems
