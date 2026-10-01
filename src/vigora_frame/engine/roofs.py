"""Coberturas e treliças (seção 9.3, Anexo A6).

Cada treliça é gerada no plano local (x ao longo do vão a partir da face externa
da parede de apoio, y vertical a partir da base do banzo inferior). As peças são
polígonos exatos: retângulo da barra recortado pelas faces das barras vizinhas,
com eixos concorrentes nos nós (regra V-033).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .. import geometry as g
from ..model import Connection, RoofSpec, TrussMark
from .context import Ctx, qty_for

BIG = 1e5


def _half_plane(p: tuple, d: tuple, keep_left: bool) -> Polygon:
    """Semiplano limitado pela reta (p, d). keep_left=True mantém o lado à esquerda de d."""
    d = g.unit(d)
    n = (-d[1], d[0]) if keep_left else (d[1], -d[0])
    a = g.sub(p, g.mul(d, BIG))
    b = g.add(p, g.mul(d, BIG))
    return Polygon([a, b, g.add(b, g.mul(n, BIG)), g.add(a, g.mul(n, BIG))])


def _strip(p0: tuple, p1: tuple, depth: float, ext: float = 5000) -> Polygon:
    d = g.unit(g.sub(p1, p0))
    n = (-d[1] * depth / 2, d[0] * depth / 2)
    a = g.sub(p0, g.mul(d, ext))
    b = g.add(p1, g.mul(d, ext))
    return Polygon([g.add(a, n), g.add(b, n), g.sub(b, n), g.sub(a, n)])


@dataclass
class Part:
    role: str
    item: str
    poly: Polygon
    axis: tuple   # (p0, p1)
    ends: tuple   # nós
    angle_a: float = 90.0
    angle_b: float = 90.0
    splice: bool = False

    @property
    def cut_length(self) -> float:
        d = g.unit(g.sub(self.axis[1], self.axis[0]))
        proj = [g.dot(c, d) for c in self.poly.exterior.coords]
        return max(proj) - min(proj)


def truss_geometry(kind: str, span: float, pitch_deg: float, overhang: float, top: str, bot: str, web: str,
                   cat, spacing_studs: float | None = None) -> tuple[list[Part], dict]:
    tan = math.tan(math.radians(pitch_deg))
    cos = math.cos(math.radians(pitch_deg))
    dt, db, dw = cat.depth(top), cat.depth(bot), cat.depth(web)
    h = span / 2 if kind != "mono" else span
    mono = kind == "mono"

    def top_face(x):     # face inferior do banzo superior
        return db + (x if (mono or x <= h) else span - x) * tan

    def top_center(x):
        return top_face(x) + dt / (2 * cos)

    B = lambda x: (x, db / 2)
    T = lambda x: (x, top_center(x))
    # faces
    left_face = ((0.0, db), (cos, math.sin(math.radians(pitch_deg))))
    right_face = ((span, db), (-cos, math.sin(math.radians(pitch_deg))))
    below_left = _half_plane(left_face[0], left_face[1], keep_left=False)
    below_right = _half_plane(right_face[0], right_face[1], keep_left=True)
    above_bottom = _half_plane((0, db), (1, 0), keep_left=True)
    parts: list[Part] = []

    # banzo inferior
    bpoly = _strip(B(0), B(span), db, ext=span).intersection(below_left)
    if not mono:
        bpoly = bpoly.intersection(below_right)
    else:
        bpoly = bpoly.intersection(_half_plane((span, 0), (0, 1), keep_left=True))
    parts.append(Part("BOTTOM_CHORD", bot, bpoly, (B(0), B(span)), ("heelL", "heelR")))
    # banzos superiores
    tl0 = (-overhang, top_center(0) - overhang * tan)
    if mono:
        tl1 = (span, top_center(span))
        poly = _strip(tl0, tl1, dt).intersection(_half_plane((-overhang, 0), (0, 1), keep_left=False))
        poly = poly.intersection(_half_plane((span, 0), (0, 1), keep_left=True))
        parts.append(Part("TOP_CHORD", top, poly, (tl0, tl1), ("tail", "high")))
    else:
        tl1 = (h, top_center(h))
        poly = _strip(tl0, tl1, dt).intersection(_half_plane((-overhang, 0), (0, 1), keep_left=False))
        poly = poly.intersection(_half_plane((h, 0), (0, 1), keep_left=True))
        parts.append(Part("TOP_CHORD", top, poly, (tl0, tl1), ("tailL", "peak")))
        tr0 = (span + overhang, top_center(span) - overhang * tan)
        poly = _strip(tl1, tr0, dt).intersection(_half_plane((span + overhang, 0), (0, 1), keep_left=True))
        poly = poly.intersection(_half_plane((h, 0), (0, 1), keep_left=False))
        parts.append(Part("TOP_CHORD", top, poly, (tl1, tr0), ("peak", "tailR")))

    # emendas de banzo em nó quando o banzo passa da barra comercial (ligação com chapa no nó)
    def splice(role, item, xs_nodes):
        stock = max(cat.stock_lengths(item))
        out = []
        queue = [p for p in parts if p.role == role]
        while queue:
            pt = queue.pop(0)
            if pt.cut_length <= stock + 0.5:
                out.append(pt)
                continue
            xs_ = [c[0] for c in pt.poly.exterior.coords]
            mid = (min(xs_) + max(xs_)) / 2
            cand = [x for x in xs_nodes if min(xs_) + 300 < x < max(xs_) - 300]
            if not cand:
                out.append(pt)
                continue
            xc = min(cand, key=lambda x: abs(x - mid))
            a = pt.poly.intersection(_half_plane((xc, 0), (0, 1), keep_left=False))
            b = pt.poly.intersection(_half_plane((xc, 0), (0, 1), keep_left=True))
            for piece in (a, b):
                np_ = Part(role, item, piece, pt.axis, pt.ends)
                np_.splice = True
                queue.append(np_)
        parts[:] = [p for p in parts if p.role != role] + out

    # diagonais e montantes (nós concorrentes nos eixos)
    webs: list[tuple] = []
    S = span
    if kind == "kingpost":
        webs = [(B(h), T(h))]
    elif kind == "fink":
        webs = [(T(S / 4), B(S / 3)), (B(S / 3), T(h)), (T(h), B(2 * S / 3)), (B(2 * S / 3), T(3 * S / 4))]
    elif kind == "howe":
        webs = [(B(S / 4), T(S / 4)), (T(S / 4), B(h)), (B(h), T(h)), (B(h), T(3 * S / 4)), (B(3 * S / 4), T(3 * S / 4))]
    elif kind == "pratt":
        webs = [(B(S / 4), T(S / 4)), (B(S / 4), T(h)), (B(h), T(h)), (T(h), B(3 * S / 4)), (B(3 * S / 4), T(3 * S / 4))]
    elif kind == "mono":
        n = max(2, math.ceil(S / 2000))
        for i in range(1, n):
            xi = S * i / n
            webs.append((B(xi), T(xi)))
            webs.append((B(xi), T(S * (i + 1) / n) if i + 1 < n else T(S - dw / 2)))
        webs.append((B(S - dw / 2), T(S - dw / 2)))
    elif kind == "gable":
        sp = spacing_studs or 400
        k = 1
        while k * sp < S - dw:
            x = k * sp
            if top_face(x) - db > 60:
                webs.append((B(x), T(x)))
            k += 1
    else:
        raise ValueError(f"tipo de treliça desconhecido: {kind}")

    # recorte das barras de alma
    container = above_bottom.intersection(below_left)
    if not mono:
        container = container.intersection(below_right)
    node_webs: dict[tuple, list[int]] = {}
    for i, (p, q) in enumerate(webs):
        node_webs.setdefault((round(p[0], 3), round(p[1], 3)), []).append(i)
        node_webs.setdefault((round(q[0], 3), round(q[1], 3)), []).append(i)
    role = "GABLE_STUD" if kind == "gable" else "WEB"
    for i, (p, q) in enumerate(webs):
        poly = _strip(p, q, dw).intersection(container)
        for node in (p, q):
            others = [j for j in node_webs[(round(node[0], 3), round(node[1], 3))] if j != i]
            my_dir = g.unit(g.sub(q, p) if node == p else g.sub(p, q))
            for j in others:
                op, oq = webs[j]
                o_dir = g.unit(g.sub(oq, op) if (round(op[0], 3), round(op[1], 3)) == (round(node[0], 3), round(node[1], 3)) else g.sub(op, oq))
                bis = g.unit(g.add(my_dir, o_dir))
                # reta bissetriz passa pelo nó; mantém o lado do meu eixo
                side = g.cross(bis, my_dir) > 0
                poly = poly.intersection(_half_plane(node, bis, keep_left=side))
        if poly.is_empty:
            continue
        d = g.sub(q, p)
        ang = math.degrees(math.atan2(abs(d[1]), abs(d[0]))) if d[0] else 90.0
        parts.append(Part(role, web, poly, (p, q), (p, q), angle_a=round(ang, 1), angle_b=round(ang, 1)))

    bnodes = sorted({round(p[0], 2) for w_ in webs for p in w_ if abs(p[1] - db / 2) < 1})
    tnodes = sorted({round(p[0], 2) for w_ in webs for p in w_ if abs(p[1] - db / 2) >= 1})
    splice("BOTTOM_CHORD", bot, bnodes)
    splice("TOP_CHORD", top, tnodes)
    nodes = set()
    for p, q in webs:
        nodes.add((round(p[0]), round(p[1])))
        nodes.add((round(q[0]), round(q[1])))
    height = max(c[1] for pt in parts for c in pt.poly.exterior.coords)
    info = {"rise": (h * tan), "height": height, "nodes": len(nodes) + (2 if not mono else 3) + (0 if mono else 1)}
    return parts, info


def profile_truss(surface: list, S: float, right_end: str, top: str, bot: str, web: str, cat,
                  max_panel: float = 1800.0, left_end: str = "heel", keepout=None) -> tuple[list[Part], dict]:
    """Treliça genérica a partir da linha do telhado (superfície superior dos banzos).

    surface: pontos (x, y) da face superior do banzo superior, de -beiral até a ponta direita.
    right_end: "heel" (apoio com beiral, como na esquerda) ou "square" (ponta reta: pendurada na mestra).
    Montantes em todos os nós, diagonais nos painéis, tudo recortado nas faces (sem sobreposição).
    """
    dt, db, dw = cat.depth(top), cat.depth(bot), cat.depth(web)
    parts: list[Part] = []
    # banzo superior: um trecho por segmento da linha do telhado, faces paralelas, corte a prumo entre trechos
    segs, bottoms = [], []
    for (xa, ya), (xb, yb) in zip(surface, surface[1:]):
        d = g.unit((xb - xa, yb - ya))
        n = (d[1], -d[0])                                  # normal para baixo
        a2, b2 = (xa + n[0] * dt, ya + n[1] * dt), (xb + n[0] * dt, yb + n[1] * dt)
        # face inferior como reta; alturas nos limites do trecho
        def yb_at(x, a2=a2, b2=b2):
            return a2[1] + (b2[1] - a2[1]) * (x - a2[0]) / (b2[0] - a2[0])
        band = Polygon([(xa, -BIG), (xb, -BIG), (xb, BIG), (xa, BIG)])
        strip = Polygon([g.sub((xa, ya), g.mul(d, BIG)), g.add((xb, yb), g.mul(d, BIG)),
                         g.add(b2, g.mul(d, BIG)), g.sub(a2, g.mul(d, BIG))])
        segs.append(Part("TOP_CHORD", top, strip.intersection(band), ((xa, ya), (xb, yb)), ("", "")))
        bottoms.append((xa, xb, yb_at))
    parts += segs

    def bf(x):                                            # face inferior do banzo superior em x
        for xa, xb, f in bottoms:
            if xa - 1e-6 <= x <= xb + 1e-6:
                return f(x)
        return bottoms[-1][2](x)

    # recipiente das barras de alma: abaixo das faces inferiores, acima do banzo inferior, dentro do vão
    pts = [(surface[0][0], -BIG)]
    for xa, xb, f in bottoms:
        pts += [(xa, f(xa)), (xb, f(xb))]
    pts.append((surface[-1][0], -BIG))
    under = Polygon(pts).buffer(0)
    container = under.intersection(Polygon([(0, db), (S, db), (S, BIG), (0, BIG)]))
    # banzo inferior: bisel no apoio sob o banzo superior; ponta reta na mestra
    xl = 0.0 if left_end == "square" else -BIG
    xr = S if right_end == "square" else S + BIG
    bpoly = Polygon([(xl, 0), (xr, 0), (xr, db), (xl, db)]).intersection(under)
    parts.append(Part("BOTTOM_CHORD", bot, bpoly, ((0, db / 2), (S, db / 2)), ("", "")))

    # nós: quebras da linha do telhado + subdivisão até max_panel
    breaks = sorted({round(x, 3) for x, _ in surface if 1.0 < x < S - 1.0})
    keys = [0.0] + breaks + [S]
    nodes = []
    for a, b in zip(keys, keys[1:]):
        n = max(1, math.ceil((b - a) / max_panel - 1e-9))
        nodes += [a + (b - a) * i / n for i in range(n)]
    nodes = sorted(set(round(x, 3) for x in nodes + [S]))
    must = set()
    if keepout is not None:                  # área livre (caixa d'água): montantes nas bordas, nada dentro
        kx0, kx1 = keepout[0], keepout[1]
        must = {round(kx0 - dw / 2, 3), round(kx1 + dw / 2, 3)}
        nodes = sorted({x for x in nodes if not (kx0 - dw - 60 < x < kx1 + dw + 60)} |
                       {x for x in must if 0 < x < S})
    # nós próximos demais (montantes se tocariam ou ficariam com vão < 60 mm): mantém o primeiro
    kept = [nodes[0]]
    for x in nodes[1:-1]:
        if x in must:
            if kept and x - kept[-1] < dw + 60 and kept[-1] not in must and len(kept) > 1:
                kept.pop()
            kept.append(x)
        elif x - kept[-1] >= dw + 60 and (S - x) >= dw + 60:
            kept.append(x)
    nodes = kept + [nodes[-1]]
    verts = {}
    for x in nodes[1:-1]:
        h = bf(x) - db
        if h < 80:
            continue
        v = Polygon([(x - dw / 2, -BIG), (x + dw / 2, -BIG), (x + dw / 2, BIG), (x - dw / 2, BIG)]).intersection(container)
        if v.area > 0:
            verts[x] = (x - dw / 2, x + dw / 2)
            parts.append(Part("WEB", web, v, ((x, db), (x, bf(x))), ("", "")))
    if right_end == "square":
        v = Polygon([(S - dw, -BIG), (S, -BIG), (S, BIG), (S - dw, BIG)]).intersection(container)
        verts[S] = (S - dw, S)
        parts.append(Part("WEB", web, v, ((S - dw / 2, db), (S - dw / 2, bf(S - dw / 2))), ("", "")))
    if left_end == "square":
        v = Polygon([(0, -BIG), (dw, -BIG), (dw, BIG), (0, BIG)]).intersection(container)
        verts[0.0] = (0.0, dw)
        parts.append(Part("WEB", web, v, ((dw / 2, db), (dw / 2, bf(dw / 2))), ("", "")))
    # diagonais
    mid = S / 2 if right_end == "heel" else S
    xs_v = sorted(verts)
    for a, b in zip(xs_v, xs_v[1:]):
        if a <= 1.0 and left_end != "square":
            continue
        if keepout is not None and a < keepout[1] and b > keepout[0]:
            continue                             # painel da abertura: sem diagonal
        if (a + b) / 2 <= mid:
            p0, p1 = (a, db / 2), (b, bf(b))
        else:
            p0, p1 = (b, db / 2), (a, bf(a))
        poly = _strip(p0, p1, dw).intersection(container)
        poly = poly.intersection(Polygon([(verts[a][1], -BIG), (verts[b][0], -BIG), (verts[b][0], BIG), (verts[a][1], BIG)]))
        if poly.is_empty or poly.area < dw * 120:
            continue
        pr = Part("WEB", web, poly, (p0, p1), ("", ""))
        if pr.cut_length < 150:
            continue
        d = g.sub(p1, p0)
        ang = math.degrees(math.atan2(abs(d[1]), abs(d[0])))
        pr.angle_a = pr.angle_b = round(ang, 1)
        parts.append(pr)

    # emendas de banzo em nó quando passam da barra comercial
    for role, item in (("BOTTOM_CHORD", bot), ("TOP_CHORD", top)):
        stock = max(cat.stock_lengths(item))
        out, queue = [], [p for p in parts if p.role == role]
        while queue:
            pt = queue.pop(0)
            if pt.cut_length <= stock + 0.5:
                out.append(pt)
                continue
            xs_ = [c[0] for c in pt.poly.exterior.coords]
            cand = [x for x in nodes if min(xs_) + 300 < x < max(xs_) - 300]
            if not cand:
                out.append(pt)
                continue
            xc = min(cand, key=lambda x: abs(x - (min(xs_) + max(xs_)) / 2))
            for piece in (pt.poly.intersection(_half_plane((xc, 0), (0, 1), keep_left=False)),
                          pt.poly.intersection(_half_plane((xc, 0), (0, 1), keep_left=True))):
                np_ = Part(role, item, piece, pt.axis, pt.ends)
                np_.splice = True
                queue.append(np_)
        parts[:] = [p for p in parts if p.role != role] + out
    if keepout is not None:                  # segurança: nenhuma barra de alma dentro da área livre
        ko = Polygon([(keepout[0], keepout[2]), (keepout[1], keepout[2]), (keepout[1], keepout[3]),
                      (keepout[0], keepout[3])])
        parts[:] = [p for p in parts if p.role != "WEB" or p.poly.intersection(ko).area < 1.0]
    height = max(c[1] for pt in parts for c in pt.poly.exterior.coords)
    return parts, {"height": height, "nodes": len(nodes) + len(breaks) + 2,
                   "rise": max(y for _, y in surface) - surface[0][1], "surface": surface, "S": S,
                   "left_end": left_end, "right_end": right_end}


def choose_type(rs: RoofSpec, span: float, ctx: Ctx) -> dict | None:
    Rr = ctx.rules.data["roof"]
    if rs.kind == "mono":
        return {"type": "mono", "span_min": 0, "span_max": Rr["mono"]["span_max"], **Rr["mono"]}
    for row in Rr["truss_table"]:
        if rs.truss_type and row["type"] == rs.truss_type:
            return row
        if not rs.truss_type and row["span_min"] <= span < row["span_max"]:
            return row
    return None


def _grid(start: float, end: float, step: float, origin_global: float) -> list[float]:
    """Posições locais (a partir de start) que caem na grade global do projeto."""
    p = (-origin_global) % step
    out = []
    while p <= end + 1e-6:
        if p >= start - 1e-6:
            out.append(p)
        p += step
    return out


def frame_roof(rs: RoofSpec, ctx: Ctx, wall_frames: list) -> None:
    Rr = ctx.rules.data["roof"]
    cat = ctx.cat
    rid = f"{ctx.pfx}-{rs.level}-{rs.id}"
    ext = [wf for wf in wall_frames if wf.wall.exterior]
    if rs.outline:
        xs = [p[0] for p in rs.outline]
        ys = [p[1] for p in rs.outline]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    else:
        pts = []
        for wf in ext:
            nrm = (-wf.dirv[1] * wf.depth / 2, wf.dirv[0] * wf.depth / 2)
            for q in (wf.origin, wf.to_global(wf.L)):
                pts += [g.add(q, nrm), g.sub(q, nrm)]
        minx = min(p[0] for p in pts)
        maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts)
        maxy = max(p[1] for p in pts)
    if rs.ridge_axis == "x":
        span, Lr, o_along, o_span = maxy - miny, maxx - minx, minx, miny
    else:
        span, Lr, o_along, o_span = maxx - minx, maxy - miny, miny, minx
    span_type = span
    if rs.support == "parapet":
        span_type = span - 2 * max((wf.depth for wf in ext), default=140)
    elif rs.support == "high_wall":
        span_type = span - max((wf.depth for wf in ext), default=140)
    row = choose_type(rs, span_type, ctx)
    if row is None:
        ctx.issue("V-032", "error", rid, f"vão de {span:.0f} mm sem tipo de treliça na tabela")
        return
    if not (row["span_min"] <= span_type < row["span_max"]):
        ctx.issue("V-032", "error", rid, f"tipo {row['type']} fora da faixa de vão ({span_type:.0f} mm)")
    ovh = rs.overhang if rs.overhang is not None else Rr["overhang"]
    sp = rs.spacing or Rr["spacing"]
    tanp = math.tan(math.radians(rs.pitch_deg))
    cosp = math.cos(math.radians(rs.pitch_deg))
    top, bot, web = row["top"], row["bottom"], row["web"]
    # telhado encostado/rincão: banzos com a mesma altura do principal -> apoio e beiral na mesma cota
    if rs.outline and any(e_ in ("valley", "abut") for e_ in rs.ends):
        for info_m in ctx.roof_info.values():
            if info_m["level"] == rs.level and cat.depth(info_m["bot"]) > cat.depth(bot) - 0.5:
                if cat.depth(info_m["bot"]) != cat.depth(bot) or cat.depth(info_m["top"]) != cat.depth(top):
                    ctx.issue("V-000", "info", rid, f"banzos iguais ao telhado principal ({info_m['top']}/{info_m['bot']}) "
                                                    "para alinhar apoio e beiral")
                bot, top = (info_m["bot"] if cat.depth(info_m["bot"]) >= cat.depth(bot) else bot,
                            info_m["top"] if cat.depth(info_m["top"]) >= cat.depth(top) else top)
                break
    dt_top, db_bot = cat.depth(top), cat.depth(bot)
    t_face = cat.face(top)

    # --- apoio: paredes portantes nas faces do vão (e paredes de topo no 4 águas)
    lv_elev = ctx.project.levels[[l.id for l in ctx.project.levels].index(rs.level)].elevation
    mono_flip = rs.kind == "mono" and rs.high_side == "start"

    def walls_on_face(face, along_ridge=True):
        out = []
        for wf in wall_frames:
            if (wf.axis == rs.ridge_axis) != along_ridge:
                continue
            c = (wf.origin[1] if wf.axis == "x" else wf.origin[0])
            a0, a1 = sorted(((wf.origin[0], wf.to_global(wf.L)[0]) if wf.axis == "x" else (wf.origin[1], wf.to_global(wf.L)[1])))
            lo_, hi_ = (o_along, o_along + Lr) if along_ridge else (o_span, o_span + span)
            if a0 < hi_ - 1 and a1 > lo_ + 1 and abs(abs(c - face) - wf.depth / 2) < 1.0:
                out.append(wf)
        return out
    low_face = o_span + span if mono_flip else o_span
    high_face = o_span if mono_flip else o_span + span
    S_in = span                 # vão livre da treliça
    x_shift = 0.0               # deslocamento da origem local (platibanda: face interna)
    hang = (False, False)       # pontas penduradas (esquerda, direita)
    if rs.support == "parapet":
        if rs.bearing_height is None:
            ctx.issue("V-086", "error", rid, "platibanda sem 'bearing_height' (altura do banzo inferior)")
            return
        wl, wr = walls_on_face(o_span), walls_on_face(o_span + span)
        dl = max((w_.depth for w_ in wl), default=140)
        dr = max((w_.depth for w_ in wr), default=140)
        S_in, x_shift, hang = span - dl - dr, dl, (True, True)
        z_top = lv_elev + rs.bearing_height
        ovh = 0.0
    else:
        bearing = [w_ for w_ in walls_on_face(low_face) if w_.wall.bearing]
        if rs.support == "high_wall":
            if rs.kind != "mono":
                ctx.issue("V-086", "error", rid, "parede alta só se aplica à meia-água")
                return
            hw_ = walls_on_face(high_face)
            if not hw_:
                ctx.issue("V-086", "error", rid, "meia-água sem parede alta no lado alto")
                return
            S_in, hang = span - max(w_.depth for w_ in hw_), (False, True)
        else:
            bearing += [w_ for w_ in walls_on_face(high_face) if w_.wall.bearing]
            if rs.kind == "hip":
                bearing += [w_ for f_ in (o_along, o_along + Lr) for w_ in walls_on_face(f_, along_ridge=False)
                            if w_.wall.bearing]
        tops = [w_.H for w_ in bearing]
        if not tops:
            ctx.issue("V-080", "error", rid, "cobertura sem paredes portantes de apoio")
            tops = [max((wf.H for wf in ext), default=2700)]
        if max(tops) - min(tops) > 1.0:
            ctx.issue("V-076", "error", rid, f"paredes de apoio com alturas diferentes ({min(tops):.0f} e {max(tops):.0f} mm)")
        z_top = lv_elev + max(tops)
    T0 = db_bot + dt_top / cosp

    def T(x):
        return T0 + x * tanp

    def surf_gable(trunc=None, S=span, ol=None, orr=None):
        """Linha do telhado de duas águas (truncada no recuo 'trunc'; beirais esquerdo/direito)."""
        ol = ovh if ol is None else ol
        orr = ovh if orr is None else orr
        a = S / 2 if trunc is None else min(trunc, S / 2)
        pts = [(-ol, T(-ol)), (a, T(a))]
        if a < S / 2 - 1:
            pts.append((S - a, T(a)))
        pts.append((S + orr, T(-orr)))
        return pts

    # --- beiral cortado onde outro telhado encosta na linha de beiral (asa em L/T/U)
    cut = {"l": [], "r": []}
    for other in ctx.project.roofs:
        if other.id == rs.id or other.level != rs.level or not other.outline:
            continue
        oxs = [q[0] for q in other.outline]
        oys = [q[1] for q in other.outline]
        o_sp = (min(oys), max(oys)) if rs.ridge_axis == "x" else (min(oxs), max(oxs))
        o_al = (min(oxs), max(oxs)) if rs.ridge_axis == "x" else (min(oys), max(oys))
        if abs(o_sp[1] - o_span) < 1:
            cut["r" if mono_flip else "l"].append((o_al[0] - o_along, o_al[1] - o_along))
        if abs(o_sp[0] - (o_span + span)) < 1:
            cut["l" if mono_flip else "r"].append((o_al[0] - o_along, o_al[1] - o_along))

    def cuts_at(p):
        return (any(a - t_face <= p <= b + t_face for a, b in cut["l"]),
                any(a - t_face <= p <= b + t_face for a, b in cut["r"]))

    wall_sp = min((wf.spacing for wf in ext), default=400)
    placed = []                 # (prefixo, peças, info, posição ao longo, extra)
    if rs.support == "parapet":
        if rs.kind == "mono":
            surf = [(0.0, T(0)), (S_in, T(S_in))]
        else:
            surf = [(0.0, T(0)), (S_in / 2, T(S_in / 2)), (S_in, T(0))]
        parts, info = profile_truss(surf, S_in, "square", top, bot, web, cat, left_end="square")
        el, er = walls_on_face(o_along, False), walls_on_face(o_along + Lr, False)
        a0 = max((w_.depth for w_ in el), default=140) + t_face / 2
        a1 = Lr - max((w_.depth for w_ in er), default=140) - t_face / 2
        pos = [a0] + [q for q in _grid(a0 + t_face + 1, a1 - t_face - 1, sp, o_along)] + [a1]
        for p in pos:
            placed.append(("T", parts, info, p, None))
    elif rs.kind in ("gable", "mono"):
        if rs.support == "high_wall":
            common, cinfo = profile_truss([(-ovh, T(-ovh)), (S_in, T(S_in))], S_in, "square", top, bot, web, cat)
            gparts, ginfo = common, cinfo
        else:
            common, cinfo = truss_geometry(row["type"], span, rs.pitch_deg, ovh, top, bot, web, cat)
            gab = Rr["gable"]
            gparts, ginfo = truss_geometry("gable" if rs.kind != "mono" else "mono", span, rs.pitch_deg, ovh, gab["top"],
                                           gab["bottom"], gab["web"], cat, spacing_studs=wall_sp)
        d_end = max((wf.depth for wf in ext), default=140)
        e0, e1 = rs.ends
        first = d_end / 2 if e0 == "gable" else t_face / 2
        last = Lr - (d_end / 2 if e1 == "gable" else t_face / 2)
        seq = [(first, e0)] + [(q, "mid") for q in _grid(first + t_face + 1, last - t_face - 1, sp, o_along)] + [(last, e1)]
        for p, kind_ in seq:
            gable_end = kind_ == "gable"
            cl, cr = cuts_at(p)
            if (cl or cr) and rs.kind == "gable" and rs.support == "walls":
                parts, info = profile_truss(surf_gable(None, span, 0.0 if cl else ovh, 0.0 if cr else ovh), span, "heel",
                                            top, bot, web, cat, max_panel=wall_sp if gable_end else 1800.0)
                placed.append(("G" if gable_end else "T", parts, info, p, None))
            else:
                placed.append(("G" if gable_end else "T", gparts if gable_end else common,
                               ginfo if gable_end else cinfo, p, None))
    else:   # hip
        g0 = rs.girder_setback or max(1200.0, span / 4)
        grid_pos = _grid(0, Lr, sp, o_along)
        p1 = min([p for p in grid_pos if p >= g0] or [g0])
        p2 = max([p for p in grid_pos if p <= Lr - g0] or [Lr - g0])
        if p2 - p1 < sp:
            ctx.issue("V-081", "error", rid, "planta curta demais para 4 águas com este recuo de mestra")
            return
        common, cinfo = truss_geometry(row["type"], span, rs.pitch_deg, ovh, top, bot, web, cat)
        for p in sorted(set([p1, p2] + [q for q in grid_pos if p1 < q < p2])):
            a = min(p, Lr - p)
            cl, cr = cuts_at(p)
            girder = p in (p1, p2)
            if a >= span / 2 - 1 and not (cl or cr):
                placed.append(("T", common, cinfo, p, None))
                continue
            parts, info = profile_truss(surf_gable(a if a < span / 2 - 1 else None, span, 0.0 if cl else ovh,
                                                   0.0 if cr else ovh), span, "heel", top, bot, web, cat)
            pf = "M" if girder else ("D" if a < span / 2 - 1 else "T")
            placed.append((pf, parts, info, p, "girder" if girder else None))
        plies_g = 2
        for end, pg in (("start", p1), ("end", p2)):
            Lj = (pg if end == "start" else Lr - pg) - plies_g * t_face / 2
            for b in _grid(0, span, sp, o_span):
                bt = min(b, span - b)
                if bt < 150:
                    continue
                pts = [(-ovh, T(-ovh))]
                if bt < Lj - 1:
                    pts += [(bt, T(bt)), (Lj, T(bt))]
                else:
                    pts += [(Lj, T(Lj))]
                parts, info = profile_truss(pts, Lj, "square", top, bot, web, cat)
                placed.append(("J", parts, info, b, end))
        hip_plan = (span / 2 + ovh) * math.sqrt(2)
        hip_pitch = math.atan(tanp / math.sqrt(2))
        L_hip = hip_plan / math.cos(hip_pitch)
        n_pc = math.ceil(L_hip / max(cat.stock_lengths(top)) - 1e-9)
        for k in range(4):
            for j in range(n_pc):
                m = ctx.new_member("HIP_RAFTER", top, rs.level, "roof", rid, frame="plan",
                                   cut_length=round(L_hip / n_pc, 1), orientation="H", rule="roof.hip",
                                   note=f"espigão {k + 1}, trecho {j + 1}/{n_pc}, inclinação {math.degrees(hip_pitch):.1f}°"
                                        + (", emenda sobre a quebra da treliça" if n_pc > 1 else ""))
                m.id = f"{rid}-HIP_RAFTER-{k + 1:02d}{chr(65 + j)}"
                ctx.members.append(m)

    # --- conjunto de rincão: treliças V sobre as águas do telhado principal (asa com ponta "valley")
    for ei, e_ in enumerate(rs.ends):
        if e_ != "valley" or rs.kind != "gable":
            continue
        face = o_along if ei == 0 else o_along + Lr
        dirv = -1.0 if ei == 0 else 1.0
        main = None
        for info_m in ctx.roof_info.values():
            if info_m["level"] != rs.level or info_m["ridge_axis"] == rs.ridge_axis:
                continue
            for side_face in (info_m["o_span"], info_m["o_span"] + info_m["span"]):
                if abs(side_face - face) < 1:
                    main = info_m
        if main is None:
            ctx.issue("V-088", "error", rid, "ponta de rincão sem telhado principal perpendicular encostado")
            continue
        ridge_w = z_top + T(span / 2)
        if ridge_w > main["ridge_z"] - 1:
            ctx.issue("V-088", "error", rid, f"cumeeira da asa ({ridge_w:.0f}) acima da cumeeira principal "
                                             f"({main['ridge_z']:.0f}): rincão impossível")
            continue

        def main_surface(q):     # altura da superfície do principal na coordenada 'q' (ao longo da asa)
            s_m = q - main["o_span"]
            if main["kind"] == "mono":
                s_eff = (main["span"] - s_m) if main["flip"] else s_m
            else:
                s_eff = min(s_m, main["span"] - s_m)
            return main["z_top"] + main["T0"] + s_eff * main["tan"]
        u = sp
        n_v = 0
        while True:
            q = face + dirv * u
            base = main_surface(q)
            Tv = dt_top / cosp                     # ponta afinada: banzo inferior chanfrado sob o superior
            v_a = (base + Tv - z_top - T0) / tanp
            span_v = span - 2 * v_a
            if span_v < 450 or v_a < 0:
                break
            surf = [(0.0, Tv), (span_v / 2, Tv + span_v / 2 * tanp), (span_v, Tv)]
            parts, info = profile_truss(surf, span_v, "heel", top, bot, web, cat)
            p_local = q - o_along
            placed.append(("V", parts, info, p_local, {"z": base, "v0": v_a}))
            n_v += 1
            u += sp
        ctx.issue("V-000", "info", rid, f"rincão: {n_v} treliças V sobre o telhado principal "
                                        f"(banzo inferior chanfrado a {main['pitch']:.0f}° apoiado nas treliças de baixo)")

    ctx.roof_info[rid] = {"level": rs.level, "ridge_axis": rs.ridge_axis, "o_span": o_span, "span": span,
                          "o_along": o_along, "Lr": Lr, "z_top": z_top, "T0": T0, "tan": tanp, "kind": rs.kind,
                          "flip": mono_flip, "pitch": rs.pitch_deg, "ovh": ovh, "top": top, "bot": bot,
                          "eave_z": z_top + T(-ovh), "support": rs.support,
                          "ridge_z": z_top + (T(span / 2) if rs.kind in ("gable", "hip") else T(S_in))}

    # --- verificações da parede alta e da platibanda
    if rs.support in ("high_wall", "parapet"):
        checks = []
        if rs.support == "high_wall":
            checks = [(w_, T(S_in) + 0.0) for w_ in walls_on_face(high_face)]
        else:
            top_roof = T(S_in) if rs.kind == "mono" else T(S_in / 2)
            for f_, h_need in ((o_span, T(0) if (rs.kind == "gable" or not mono_flip) else T(S_in)),
                               (o_span + span, T(S_in) if (rs.kind == "mono" and not mono_flip) else T(0))):
                checks += [(w_, h_need + rs.parapet_min) for w_ in walls_on_face(f_)]
            checks += [(w_, top_roof + rs.parapet_min) for f_ in (o_along, o_along + Lr) for w_ in walls_on_face(f_, False)]
        for w_, need in checks:
            have = lv_elev + w_.H + ctx.wall_upper.get(w_.wall.id, 0.0) - z_top
            if have < need - 1:
                ctx.issue("V-086", "error", w_.wall.id, f"parede com {w_.H + ctx.wall_upper.get(w_.wall.id, 0.0):.0f} mm fica {need - have:.0f} mm abaixo do "
                                                        f"necessário para o telhado{' e a platibanda' if rs.support == 'parapet' else ''}")
        n_led = 2 if rs.support == "parapet" else 1
        led_item = Rr.get("ledger", top)
        for kk in range(n_led):
            x_ = 0.0
            Lled = Lr
            while x_ < Lled - 1:
                L_ = min(max(cat.stock_lengths(led_item)), Lled - x_)
                m = ctx.new_member("LEDGER", led_item, rs.level, "roof", rid, frame="plan", cut_length=round(L_, 1),
                                   orientation="H", rule="roof.ledger",
                                   note=f"guia de apoio parafusada nos montantes (lado {'alto' if kk == 0 and rs.support == 'high_wall' else kk + 1})")
                ctx.members.append(m)
                x_ += L_
        ctx.issue("V-000", "info", rid, f"treliças penduradas em estribos na face das paredes "
                                        f"({'dois lados' if rs.support == 'parapet' else 'lado alto'})")


    # --- caixa d'água: treliças que cortam o envelope viram treliças de ático (abertura sem diagonais)
    zones = [zn for zn in ctx.tank_zones if zn["level"] == rs.level and zn["roof"] == rs.id]
    if zones:
        def interp(surf_, x):
            for (xa, ya), (xb, yb) in zip(surf_, surf_[1:]):
                if xa - 1e-6 <= x <= xb + 1e-6:
                    return ya + (yb - ya) * (x - xa) / (xb - xa) if xb != xa else ya
            return surf_[-1][1]
        new_placed, adapted = [], []
        for pfx, parts, info, p, extra in placed:
            hit = None
            if pfx in ("T", "G", "D", "M") and not isinstance(extra, dict):
                plane = o_along + p
                for zn in zones:
                    c_al = zn["center"][0] if rs.ridge_axis == "x" else zn["center"][1]
                    c_sp = zn["center"][1] if rs.ridge_axis == "x" else zn["center"][0]
                    dd = max(abs(plane - c_al) - t_face, 0.0)
                    if dd < zn["R"]:
                        w_ = math.sqrt(zn["R"] ** 2 - dd ** 2)
                        cs = ((o_span + span - c_sp) if mono_flip else (c_sp - o_span)) - x_shift
                        hit = (cs - w_, cs + w_, zn["z0"] - z_top, zn["z1"] - z_top, zn)
            if hit is None:
                new_placed.append((pfx, parts, info, p, extra))
                continue
            if info.get("surface") is not None:
                surf, S_, le, re_ = info["surface"], info["S"], info["left_end"], info["right_end"]
            elif rs.kind == "mono":
                surf, S_, le, re_ = [(-ovh, T(-ovh)), (span, T(span))], span, "heel", "square"
            else:
                surf, S_, le, re_ = surf_gable(), span, "heel", "heel"
            short = max(hit[3] - (interp(surf, x_) - dt_top / cosp)
                        for x_ in [hit[0] + (hit[1] - hit[0]) * k / 8 for k in range(9)] if 0 < x_ < S_)
            if short > 0.5:
                ctx.issue("V-090", "error", f"{rid}/{hit[4]['id']}",
                          f"caixa não cabe sob o telhado: faltam {short:.0f} mm no plano da treliça em "
                          f"{o_along + p:.0f} mm (mova para perto da cumeeira, aumente a inclinação ou use torre)")
            parts2, info2 = profile_truss(surf, S_, re_, top, bot, web, cat, max_panel=wall_sp if pfx == "G" else 1800.0,
                                          left_end=le, keepout=hit[:4])
            new_placed.append(("A" if pfx in ("T", "G") else pfx, parts2, info2, p, extra))
            adapted.append(round(o_along + p))
        placed = new_placed
        if adapted:
            ctx.issue("V-000", "info", rid, f"{len(adapted)} treliças viraram treliças de ático para a caixa d'água "
                                            f"(planos em {', '.join(str(a) for a in adapted)} mm)")

    lim = ctx.rules.limits["truss_transport"]
    sigs: dict = {}
    counters = ctx.__dict__.setdefault("_mark_counters", {})     # marcas únicas no projeto (vários telhados)
    marks: dict = {}
    n = 0
    for pfx, parts, info, p, extra in placed:
        n += 1
        tid = f"{rid}-TR{n:02d}"
        if pfx == "J":
            end = extra
            along_dir = (1, 0) if rs.ridge_axis == "x" else (0, 1)
            if end == "end":
                along_dir = (-along_dir[0], -along_dir[1])
            base_along = o_along if end == "start" else o_along + Lr
            o3 = (base_along, o_span + p) if rs.ridge_axis == "x" else (o_span + p, base_along)
            ctx.placements[tid] = {"origin": (o3[0], o3[1], z_top), "span_dir": along_dir}
        else:
            if mono_flip:
                o3 = (o_along + p, o_span + span) if rs.ridge_axis == "x" else (o_span + span, o_along + p)
                sd = (0, -1) if rs.ridge_axis == "x" else (-1, 0)
            else:
                o3 = (o_along + p, o_span) if rs.ridge_axis == "x" else (o_span, o_along + p)
                sd = (0, 1) if rs.ridge_axis == "x" else (1, 0)
            shift = extra["v0"] if isinstance(extra, dict) else x_shift
            o3 = (o3[0] + sd[0] * shift, o3[1] + sd[1] * shift)
            zz = extra["z"] if isinstance(extra, dict) else z_top
            ctx.placements[tid] = {"origin": (o3[0], o3[1], zz), "span_dir": sd}
        sig = pfx + repr(sorted((pt.role, round(pt.poly.area), round(pt.cut_length)) for pt in parts))
        if sig not in sigs:
            counters[pfx] = counters.get(pfx, 0) + 1
            mark = f"{pfx}{counters[pfx]}"
            sigs[sig] = mark
            kind_name = {"T": row["type"] if rs.support == "walls" else ("pendurada" if rs.support == "parapet"
                                                                              else "meia-água pendurada"),
                         "G": "oitão" if rs.kind != "mono" else "mono-oitão", "D": "truncada",
                         "M": "mestra (2 peças)", "J": "meia-tesoura", "V": "rincão",
                         "A": "ático (abertura p/ caixa d'água)"}[pfx]
            marks[mark] = TrussMark(mark=mark, type=kind_name, span=round(max(c[0] for pt in parts for c in pt.poly.exterior.coords if pt.role == "BOTTOM_CHORD"), 1),
                                    rise=round(info["rise"], 1), pitch_deg=rs.pitch_deg, count=0,
                                    height=round(info["height"], 1))
            if info["height"] > lim["max_height"]:
                ctx.issue("V-034", "warning", f"{rid}/{mark}", f"treliça com {info['height']:.0f} mm de altura acima do "
                                                               f"transporte ({lim['max_height']} mm)")
        mark = sigs[sig]
        marks[mark].count += 1
        plies = 2 if extra == "girder" else 1
        ms, cnt = [], {}
        for part in parts:
            cnt[part.role] = cnt.get(part.role, 0) + 1
            coords = [(round(x, 2), round(y, 2)) for x, y in part.poly.exterior.coords]
            m = ctx.new_member(part.role, part.item, rs.level, "roof", tid, frame="truss",
                               x0=min(c[0] for c in coords), x1=max(c[0] for c in coords),
                               z0=min(c[1] for c in coords), z1=max(c[1] for c in coords), orientation="A",
                               polygon=coords, cut_length=round(part.cut_length, 1), angle_a=part.angle_a,
                               angle_b=part.angle_b, plies=plies, rule="roof.truss_table",
                               note=f"marca {mark}" + ("; emenda no nó com chapa" if part.splice else ""))
            m.id = f"{tid}-{part.role}-{cnt[part.role]:02d}"
            ms.append(m)
        if not marks[mark].member_ids:
            marks[mark].member_ids = [m.id for m in ms]
        ctx.members += ms
        polys = [Polygon(m.polygon) for m in ms]
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                inter = polys[i].intersection(polys[j]).area
                if inter > 50:
                    ctx.issue("V-061", "error", tid, f"sobreposição de {inter:.0f} mm² entre {ms[i].id} e {ms[j].id}")
                if polys[i].distance(polys[j]) <= 1.0:
                    ctx._seq += 1
                    ctx.connections.append(Connection(id=f"C{ctx._seq}", a=ms[i].id, b=ms[j].id, type="LG-11",
                                                      fastener=Rr["plate"], qty=2))
        ctx.hw(Rr["plate"], info["nodes"] * 2, f"{tid} chapas dos nós (2 faces)")
        # apoios
        o3, sd = ctx.placements[tid]["origin"], ctx.placements[tid]["span_dir"]
        span_here = max(c[0] for pt in parts for c in pt.poly.exterior.coords if pt.role == "BOTTOM_CHORD")
        if pfx == "V":
            ctx.hw(ctx.rules.data["anchorage"]["roof_uplift"]["item"], 2, f"{tid} presilhas nas treliças de baixo")
            continue
        if hang[0] or hang[1]:
            if not hang[0]:
                ctx.bearing_points.append(("truss", tid, (o3[0], o3[1]), rs.level))
            ctx.hw("SUPORTE-VIGA-SV1", int(hang[0]) + int(hang[1]), f"{tid} estribos na face da parede")
            ctx.hw(ctx.rules.data["anchorage"]["roof_uplift"]["item"], 2 - int(hang[0]) - int(hang[1]),
                   f"{tid} conector no apoio")
            continue
        ctx.bearing_points.append(("truss", tid, (o3[0], o3[1]), rs.level))
        if pfx != "J":
            ctx.bearing_points.append(("truss", tid, (o3[0] + sd[0] * span, o3[1] + sd[1] * span), rs.level))
            ctx.hw(ctx.rules.data["anchorage"]["roof_uplift"]["item"], 2, f"{tid} conectores contra arrancamento")
        else:
            ctx.hw(ctx.rules.data["anchorage"]["roof_uplift"]["item"], 1, f"{tid} conector no apoio")
            ctx.hw("SUPORTE-VIGA-SV1", 1, f"{tid} estribo na treliça mestra")
    ctx.trusses += sorted(marks.values(), key=lambda m: m.mark)

    # acessórios: ripas, travamentos do banzo inferior, contraventamento do banzo superior
    slopes = {"gable": 2, "mono": 1, "hip": 4}[rs.kind]
    Lslope = ((S_in / 2 if rs.kind != "mono" else S_in) + ovh) / cosp
    rows = math.ceil(Lslope / Rr["batten_spacing"]) + 1
    bstock = max(ctx.cat.stock_lengths(Rr["batten"]))
    piece = math.floor(bstock / sp) * sp
    acc = []
    for sl in range(slopes):
        for r in range(rows):
            if rs.kind == "hip":
                h = r * Rr["batten_spacing"] * cosp            # recuo horizontal da fiada a partir do beiral
                run = (Lr + 2 * ovh - 2 * h) if sl < 2 else (span + 2 * ovh - 2 * h)
            else:
                run = Lr + 2 * ovh
            x = 0.0
            while x < run - 1:
                L = min(piece, run - x)
                acc.append(("BATTEN", Rr["batten"], L, f"água {sl + 1}, fiada {r + 1}"))
                x += L
    nr = max(1, math.ceil(span / Rr["bottom_chord_restraint_max"]) - 1)
    rstock = max(ctx.cat.stock_lengths(Rr["restraint"]))
    for r in range(nr):
        x = 0.0
        while x < Lr - 1:
            L = min(math.floor(rstock / sp) * sp, Lr - x)
            acc.append(("BC_RESTRAINT", Rr["restraint"], L, f"linha {r + 1} do banzo inferior"))
            x += L
    diag = math.hypot(4 * sp, Lslope)
    for sl in range(min(slopes, 2)):
        for e in range(2):
            acc.append(("DIAG_BRACE", Rr["restraint"], min(diag, rstock), f"água {sl + 1}, extremidade {e + 1}"))
    cnt = {}
    for role, item, L, note in acc:
        cnt[role] = cnt.get(role, 0) + 1
        m = ctx.new_member(role, item, rs.level, "roof", rid, frame="plan", cut_length=round(L, 1),
                           orientation="H", rule="roof.bracing", note=note)
        m.id = f"{rid}-{role}-{cnt[role]:03d}"
        ctx.members.append(m)


def check_roof_alignment(ctx: Ctx) -> None:
    """Beirais de telhados que se encontram na mesma altura; cumeeiras iguais quando vão e inclinação são iguais."""
    items = list(ctx.roof_info.items())
    for i, (ra, a) in enumerate(items):
        for rb, b in items[i + 1:]:
            if a["level"] != b["level"] or "walls" not in (a["support"], b["support"]):
                continue
            touch = False
            for fa in (a["o_span"], a["o_span"] + a["span"], a["o_along"], a["o_along"] + a["Lr"]):
                for fb in (b["o_span"], b["o_span"] + b["span"], b["o_along"], b["o_along"] + b["Lr"]):
                    touch = touch or abs(fa - fb) < 1
            if not touch:
                continue
            d_e = abs(a["eave_z"] - b["eave_z"])
            if d_e > 5:
                lo, hi = (a, b) if a["eave_z"] > b["eave_z"] else (b, a)      # 'lo' tem o beiral mais alto
                ovh_fix = (lo["ovh"] * lo["tan"] + (lo["eave_z"] - hi["eave_z"])) / lo["tan"] if lo["tan"] else 0
                ctx.issue("V-087", "warning", f"{ra}+{rb}", f"beirais desalinhados: {a['eave_z']:.0f} × {b['eave_z']:.0f} mm "
                                                             f"(diferença {d_e:.0f} mm). Para alinhar: beiral de "
                                                             f"{ovh_fix:.0f} mm no telhado de {lo['pitch']:g}°")
            else:
                ctx.issue("V-000", "info", f"{ra}+{rb}", f"beirais alinhados na cota {a['eave_z']:.0f} mm")
            if abs(a["span"] - b["span"]) < 1 and abs(a["pitch"] - b["pitch"]) < 0.01 and abs(a["ridge_z"] - b["ridge_z"]) > 5:
                ctx.issue("V-087", "warning", f"{ra}+{rb}", "mesmo vão e inclinação com cumeeiras em alturas diferentes")
