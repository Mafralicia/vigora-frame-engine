"""Entrepisos (seção 9.1): vigas na grade, vigas de borda, aberturas, travamentos, contrapiso.

Referencial 'plan': x0/x1 = x em planta, z0/z1 = y em planta.
"""
from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from ..model import FloorSpec, Sheet
from .context import Ctx, qty_for
from .walls import MIN_CLEAR, CLASH, TOUCH, contact, _conn

EPS = 0.01


def frame_floor(fs: FloorSpec, ctx: Ctx, walls_below: list, elevation: float) -> None:
    F = ctx.rules.data["floors"]
    cat = ctx.cat
    jitem, ritem = F["joist"], F["rim"]
    t = cat.face(jitem)
    s = float(F["spacing"])
    fid = f"{ctx.pfx}-{fs.level}-{fs.id}"
    sub_t = cat.get(F["subfloor"])["thickness"]
    z_bottom = elevation - sub_t - cat.depth(F["joist"])
    ctx.placements[fid] = {"z": z_bottom, "depth": cat.depth(F["joist"]), "subfloor": sub_t}
    tops = [wf.elevation + wf.H for wf in walls_below if wf.wall.bearing]
    for top in sorted(set(round(v, 1) for v in tops)):
        if abs(top - z_bottom) > 2.0:
            ctx.issue("V-076", "error", fid, f"fundo do entrepiso em {z_bottom:.1f} mm e topo das paredes portantes "
                                             f"em {top:.1f} mm: vão/sobreposição de {z_bottom - top:.1f} mm "
                                             f"(nível = topo da parede + viga + contrapiso)")
    outline = Polygon(fs.outline)
    if not outline.is_valid:
        ctx.issue("V-071", "error", fid, "contorno do piso inválido")
        return
    minx, miny, maxx, maxy = outline.bounds
    along_y = fs.joist_direction == "y"
    members = []

    stock_r = max(cat.stock_lengths(ritem))

    def mk_rim(role, x0, x1, y0, y1, item, rule=""):
        """Borda maior que a barra: emenda com junta no meio do vão entre vigas."""
        L = max(x1 - x0, y1 - y0)
        n = math.ceil(L / stock_r - 1e-9)
        if n <= 1:
            return mk(role, x0, x1, y0, y1, item, rule=rule)
        along = (x1 - x0) >= (y1 - y0)
        a0 = x0 if along else y0
        cuts = [a0]
        for i in range(1, n):
            j = a0 + L * i / n
            j = math.floor(j / s) * s + s / 2          # junta entre duas vigas
            cuts.append(j)
        cuts.append(a0 + L)
        for c0, c1 in zip(cuts, cuts[1:]):
            if along:
                mk(role, c0, c1, y0, y1, item, rule=rule, note="borda emendada: junta entre vigas, sobre a parede")
            else:
                mk(role, x0, x1, c0, c1, item, rule=rule, note="borda emendada: junta entre vigas, sobre a parede")

    def mk(role, x0, x1, y0, y1, item, plies=1, note="", rule=""):
        orient = "V" if (y1 - y0) >= (x1 - x0) else "H"
        cut = (y1 - y0) if orient == "V" else (x1 - x0)
        m = ctx.new_member(role, item, fs.level, "floor", fid, frame="plan", x0=round(x0, 2), x1=round(x1, 2),
                           z0=round(y0, 2), z1=round(y1, 2), orientation=orient, cut_length=round(cut, 1),
                           plies=plies, note=note, rule=rule)
        members.append(m)
        return m

    # bordas (somente arestas ortogonais)
    coords = list(outline.exterior.coords)
    for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
        if abs(y1 - y0) < EPS:          # aresta ao longo de x
            a, b = sorted((x0, x1))
            yy = y0 if y0 > miny + EPS else y0
            inside_up = outline.contains(box(a + 1, yy + 1, b - 1, yy + 2).centroid)
            yA, yB = (yy, yy + t) if inside_up else (yy - t, yy)
            if along_y:
                mk_rim("RIM", a, b, yA, yB, ritem, rule="floors.rim")
            else:
                mk_rim("RIM_SIDE", a + t, b - t, yA, yB, ritem, rule="floors.rim")
        elif abs(x1 - x0) < EPS:        # aresta ao longo de y
            a, b = sorted((y0, y1))
            inside_right = outline.contains(box(x0 + 1, a + 1, x0 + 2, b - 1).centroid)
            xA, xB = (x0, x0 + t) if inside_right else (x0 - t, x0)
            if along_y:
                mk_rim("RIM_SIDE", xA, xB, a + t, b - t, ritem, rule="floors.rim")
            else:
                mk_rim("RIM", xA, xB, a, b, ritem, rule="floors.rim")
        else:
            ctx.issue("V-072", "warning", fid, "aresta não ortogonal no contorno do piso: borda não gerada")

    inner = outline.buffer(-t, join_style=2)
    holes = [Polygon(h) for h in fs.holes]
    tp, hp = F["hole_trimmer_plies"], F["hole_header_plies"]
    blocked = []
    for i, h in enumerate(holes, start=1):
        hx0, hy0, hx1, hy1 = h.bounds
        if along_y:
            # vigas laterais (trimmers) e cabeceiras (headers)
            for xa, xb in ((hx0 - tp * t, hx0), (hx1, hx1 + tp * t)):
                seg = LineString([((xa + xb) / 2, miny - 10), ((xa + xb) / 2, maxy + 10)]).intersection(inner)
                for part in getattr(seg, "geoms", [seg]):
                    if part.length > 0:
                        ys = [c[1] for c in part.coords]
                        mk("TRIMMER", xa, xb, min(ys), max(ys), jitem, plies=1, rule="floors.hole_trimmer",
                           note=f"abertura {i}, {tp} peças lado a lado")
            for ya, yb in ((hy0 - hp * t, hy0), (hy1, hy1 + hp * t)):
                mk("FLOOR_HEADER", hx0, hx1, ya, yb, jitem, rule="floors.hole_header",
                   note=f"abertura {i}, {hp} peças")
                ctx.hw("SUPORTE-VIGA-SV1", 2, f"{fid} cabeceira da abertura {i}")
            blocked.append(box(hx0 - tp * t, hy0 - hp * t, hx1 + tp * t, hy1 + hp * t))
        else:
            for ya, yb in ((hy0 - tp * t, hy0), (hy1, hy1 + tp * t)):
                seg = LineString([(minx - 10, (ya + yb) / 2), (maxx + 10, (ya + yb) / 2)]).intersection(inner)
                for part in getattr(seg, "geoms", [seg]):
                    if part.length > 0:
                        xs = [c[0] for c in part.coords]
                        mk("TRIMMER", min(xs), max(xs), ya, yb, jitem, rule="floors.hole_trimmer")
            for xa, xb in ((hx0 - hp * t, hx0), (hx1, hx1 + hp * t)):
                mk("FLOOR_HEADER", xa, xb, hy0, hy1, jitem, rule="floors.hole_header")
                ctx.hw("SUPORTE-VIGA-SV1", 2, f"{fid} cabeceira da abertura {i}")
            blocked.append(box(hx0 - hp * t, hy0 - tp * t, hx1 + hp * t, hy1 + tp * t))
    free = inner.difference(unary_union(blocked)) if blocked else inner
    # vigas laterais maiores que a barra: junta de topo centrada sobre parede portante de baixo
    stock_j = max(cat.stock_lengths(jitem))
    for m in [m for m in members if m.role == "TRIMMER" and m.cut_length > stock_j + EPS]:
        a0, a1 = (m.z0, m.z1) if along_y else (m.x0, m.x1)
        pos = (m.x0 + m.x1) / 2 if along_y else (m.z0 + m.z1) / 2
        sups = []
        for wf in walls_below:
            if not wf.wall.bearing or (wf.axis == "x") != along_y:
                continue
            c = wf.origin[1] if along_y else wf.origin[0]
            lo_w, hi_w = sorted((wf.origin[0], wf.to_global(wf.L)[0]) if along_y else (wf.origin[1], wf.to_global(wf.L)[1]))
            if a0 + 300 < c < a1 - 300 and lo_w <= pos <= hi_w:
                sups.append(c)
        cuts, cur = [a0], a0
        for c in sorted(sups):
            if c - cur > stock_j:
                break
            if a1 - c <= stock_j or c == sorted(sups)[-1]:
                cuts.append(c)
                cur = c
                if a1 - c <= stock_j:
                    break
        cuts.append(a1)
        if any(b - a > stock_j + EPS for a, b in zip(cuts, cuts[1:])):
            continue           # sem apoio adequado: a validação V-063 acusa
        members.remove(m)
        for a, b in zip(cuts, cuts[1:]):
            if along_y:
                mk("TRIMMER", m.x0, m.x1, a, b, jitem, note=m.note + "; junta de topo sobre parede portante",
                   rule="floors.hole_trimmer")
            else:
                mk("TRIMMER", a, b, m.z0, m.z1, jitem, note=m.note + "; junta de topo sobre parede portante",
                   rule="floors.hole_trimmer")
    trimmers = [m for m in members if m.role == "TRIMMER"]

    # vigas na grade (alinhadas à grade global das paredes: origem no contorno)
    lo, hi = (minx, maxx) if along_y else (miny, maxy)
    joists = []
    p = math.ceil((lo + t) / s) * s - s
    while p + s < hi - t:
        p += s
        if p - t / 2 < lo + t + 1:
            continue
        a0, a1 = p - t / 2, p + t / 2
        if along_y:            # sem vão menor que 60 mm entre viga e viga lateral (ou borda)
            if any(a0 < m.x1 + MIN_CLEAR and a1 > m.x0 - MIN_CLEAR for m in trimmers) or a1 > hi - t - MIN_CLEAR:
                continue
            line = LineString([(p, miny - 10), (p, maxy + 10)])
        else:
            if any(a0 < m.z1 + MIN_CLEAR and a1 > m.z0 - MIN_CLEAR for m in trimmers) or a1 > hi - t - MIN_CLEAR:
                continue
            line = LineString([(minx - 10, p), (maxx + 10, p)])
        seg = line.intersection(free)
        for part in getattr(seg, "geoms", [seg]):
            if part.length < 1:
                continue
            cs = [c[1] if along_y else c[0] for c in part.coords]
            c0, c1 = min(cs), max(cs)
            touches_hole = any(abs(c0 - (b.bounds[3] if along_y else b.bounds[2])) < 1 or
                               abs(c1 - (b.bounds[1] if along_y else b.bounds[0])) < 1 for b in blocked)
            role = "TAIL_JOIST" if touches_hole else "JOIST"
            joists.append((role, p, c0, c1))

    # preenchimento: vão acima do máximo entre vigas vizinhas (ex.: ao lado das vigas da escada)
    def center(m):
        return ((m.x0 + m.x1) / 2, m.z0, m.z1) if along_y else ((m.z0 + m.z1) / 2, m.x0, m.x1)
    spans = [(p, c0, c1) for _, p, c0, c1 in joists] + [center(m) for m in members if m.role in ("TRIMMER", "RIM_SIDE")]
    lo2, hi2 = (miny, maxy) if along_y else (minx, maxx)
    need: dict = {}
    yq = lo2 + t + 25
    while yq < hi2 - t:
        pt_ = Point(((lo + hi) / 2, yq) if along_y else (yq, (lo + hi) / 2))
        cover = sorted(p for p, c0, c1 in spans if c0 <= yq <= c1)
        for a, b in zip(cover, cover[1:]):
            mid = Point(((a + b) / 2, yq) if along_y else (yq, (a + b) / 2))
            if b - a > s + EPS and free.contains(mid):
                need.setdefault((a, b), []).append(yq)
        yq += 50
    for (a, b), yl in need.items():
        n_ = math.ceil((b - a) / s - 1e-9) - 1
        for i in range(1, n_ + 1):
            p = a + (b - a) * i / (n_ + 1)
            y0, y1 = min(yl), max(yl)
            line = LineString([(p, lo2 - 10), (p, hi2 + 10)]) if along_y else LineString([(lo2 - 10, p), (hi2 + 10, p)])
            seg = line.intersection(free)
            for part in getattr(seg, "geoms", [seg]):
                if part.length > 1:
                    cs = [c[1] if along_y else c[0] for c in part.coords]
                    if min(cs) <= y1 and max(cs) >= y0:          # trecho inteiro, de apoio a apoio
                        joists.append(("TAIL_JOIST", p, min(cs), max(cs)))

    # apoios (paredes portantes abaixo, perpendiculares às vigas)
    stock = max(ctx.cat.stock_lengths(jitem))
    max_span = F["max_span"]
    for role, p, c0, c1 in joists:
        sup = [c0, c1]
        for wf in walls_below:
            if not wf.wall.bearing:
                continue
            if along_y and wf.axis == "x":
                x_a, x_b = sorted((wf.origin[0], wf.to_global(wf.L)[0]))
                yw = wf.origin[1]
                if x_a <= p <= x_b and c0 + t < yw < c1 - t:
                    sup.append(yw)
            elif not along_y and wf.axis == "y":
                y_a, y_b = sorted((wf.origin[1], wf.to_global(wf.L)[1]))
                xw = wf.origin[0]
                if y_a <= p <= y_b and c0 + t < xw < c1 - t:
                    sup.append(xw)
        sup = sorted(set(round(v, 1) for v in sup))
        spans = [b - a for a, b in zip(sup, sup[1:])]
        if max(spans) > max_span + EPS:
            ctx.issue("V-010", "error", f"{fid}@{p:.0f}", f"vão de {max(spans):.0f} mm acima do máximo {max_span} mm")
        pieces = [(c0, c1)]
        if c1 - c0 > stock + EPS:
            inner_sup = sup[1:-1]
            if not inner_sup:
                ctx.issue("V-063", "error", f"{fid}@{p:.0f}", "viga maior que a barra comercial e sem apoio para emenda")
            else:
                mid = (c0 + c1) / 2
                sp = min(inner_sup, key=lambda v: abs(v - mid))
                pieces = [(c0, sp + t), (sp - t, c1)]   # transpasse sobre o apoio
        for i, (a, b) in enumerate(pieces):
            if along_y:
                x0, x1 = (p - t / 2, p + t / 2) if i == 0 else (p + t / 2, p + 1.5 * t)
                mk(role, x0, x1, a, b, jitem, rule="floors.spacing",
                   note="emenda por transpasse sobre apoio" if len(pieces) > 1 else "")
            else:
                y0, y1 = (p - t / 2, p + t / 2) if i == 0 else (p + t / 2, p + 1.5 * t)
                mk(role, a, b, y0, y1, jitem, rule="floors.spacing",
                   note="emenda por transpasse sobre apoio" if len(pieces) > 1 else "")
        ctx.bearing_points += [("joist", f"{fid}@{p:.0f}", ((p, v) if along_y else (v, p)), fs.level) for v in sup]

    # travamento entre vigas (bridging)
    br = F["bridging_spacing"]
    js = sorted([m for m in members if m.role in ("JOIST", "TAIL_JOIST", "TRIMMER", "RIM_SIDE")],
                key=lambda m: (m.x0 if along_y else m.z0))
    lo2, hi2 = (miny, maxy) if along_y else (minx, maxx)
    rows = []
    q = lo2 + br
    while q < hi2 - br / 3:
        rows.append(q)
        q += br
    for q in rows:
        cover = [m for m in js if (m.z0 < q - t and m.z1 > q + t if along_y else m.x0 < q - t and m.x1 > q + t)]
        for a, b in zip(cover, cover[1:]):
            mid = ((a.x1 + b.x0) / 2, q) if along_y else (q, (a.z1 + b.z0) / 2)
            if any(bk.contains(Point(mid)) for bk in blocked):
                continue                       # não travar através da abertura
            # viga de borda/cabeceira a menos de 60 mm da linha: ela já trava esse vão (sem remendo nem vão)
            heads = [h_ for h_ in members if h_.role in ("FLOOR_HEADER", "RIM")]
            if along_y and any(h_.x0 < b.x0 and h_.x1 > a.x1 and h_.z0 - MIN_CLEAR < q + t / 2 and h_.z1 + MIN_CLEAR > q - t / 2
                               for h_ in heads):
                continue
            if not along_y and any(h_.z0 < b.z0 and h_.z1 > a.z1 and h_.x0 - MIN_CLEAR < q + t / 2 and h_.x1 + MIN_CLEAR > q - t / 2
                                   for h_ in heads):
                continue
            if along_y:
                gap = b.x0 - a.x1
                if gap > 20:
                    mk("BRIDGING", a.x1, b.x0, q - t / 2, q + t / 2, jitem, rule="floors.bridging_spacing")
            else:
                gap = b.z0 - a.z1
                if gap > 20:
                    mk("BRIDGING", q - t / 2, q + t / 2, a.z1, b.z0, jitem, rule="floors.bridging_spacing")

    # ids estáveis
    groups = {}
    for m in members:
        groups.setdefault(m.role, []).append(m)
    for role, ms in groups.items():
        ms.sort(key=lambda m: (round(m.x0, 1), round(m.z0, 1)))
        for i, m in enumerate(ms, start=1):
            m.id = f"{fid}-{role}-{i:03d}"
    ctx.members += members

    # ligações (contato em planta)
    code_for = {frozenset(["JOIST", "RIM"]): "LG-09", frozenset(["TAIL_JOIST", "FLOOR_HEADER"]): "LG-09"}
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            kind, clen = contact(a, b)
            if kind == "touch":
                code = "LG-15" if "BRIDGING" in (a.role, b.role) else "LG-09"
                conn = ctx.rules.connection(code) if code in ctx.rules.data["connections"] else \
                    {"fastener": ctx.rules.data["connections"]["LG-04"]["fastener"], "qty": 4}
                ctx.connections.append(_conn(ctx, a.id, b.id, code, conn, clen))
            elif kind == "clash" and not ({a.role, b.role} <= {"JOIST", "TAIL_JOIST", "TRIMMER"} and
                                           "emenda" in (a.note + b.note)):
                ctx.issue("V-061", "error", fid, f"interferência entre {a.id} e {b.id}")

    # contrapiso: placas com juntas desencontradas, lado maior perpendicular às vigas
    sitem = F["subfloor"]
    W, Hs = ctx.cat.get(sitem)["size"]
    area_floor = Polygon(fs.outline, [h for h in fs.holes]).area
    n = 0
    row = 0
    if along_y:
        long_, short_ = Hs, W   # lado de 2400 ao longo de x
        yy = miny
        while yy < maxy - EPS:
            off = (row % 2) * (long_ / 2)
            xx = minx - off
            while xx < maxx - EPS:
                cell = box(xx, yy, xx + long_, yy + short_)
                piece = cell.intersection(Polygon(fs.outline, [h for h in fs.holes]))
                if piece.area > 1e4:
                    n += 1
                    bx0, by0, bx1, by1 = piece.bounds
                    ctx.sheets.append(Sheet(id=f"{fid}-SF{n:03d}", item=sitem, parent=fid, x0=round(bx0, 1),
                                            x1=round(bx1, 1), z0=round(by0, 1), z1=round(by1, 1),
                                            area_m2=round(piece.area / 1e6, 4)))
                xx += long_
            yy += short_
            row += 1
    else:
        long_, short_ = Hs, W
        xx = minx
        while xx < maxx - EPS:
            off = (row % 2) * (long_ / 2)
            yy = miny - off
            while yy < maxy - EPS:
                cell = box(xx, yy, xx + short_, yy + long_)
                piece = cell.intersection(Polygon(fs.outline, [h for h in fs.holes]))
                if piece.area > 1e4:
                    n += 1
                    bx0, by0, bx1, by1 = piece.bounds
                    ctx.sheets.append(Sheet(id=f"{fid}-SF{n:03d}", item=sitem, parent=fid, x0=round(bx0, 1),
                                            x1=round(bx1, 1), z0=round(by0, 1), z1=round(by1, 1),
                                            area_m2=round(piece.area / 1e6, 4)))
                yy += long_
            xx += short_
            row += 1
    fasten = ctx.rules.data["sheathing"]["fastening"]
    per_m2 = (1000 / fasten["edge_pitch"]) * 1.2 + (1000 / fasten["field_pitch"]) * 2.0
    ctx.hw(fasten["fastener"], math.ceil(area_floor / 1e6 * per_m2), f"{fid} fixação do contrapiso")
