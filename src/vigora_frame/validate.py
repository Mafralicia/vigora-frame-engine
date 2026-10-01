"""Validações cruzadas (seções 14.4, A4.7, A5.7, A10.5)."""
from __future__ import annotations

from collections import defaultdict

from . import geometry as g
from .engine.context import Ctx
from .engine.walls import CLASH, MIN_CLEAR, TOUCH, VERTICAL, contact

LINEAR_EXEMPT = {"ARCH_FILLER"}
DEGREE_EXEMPT = {"CAP_PLATE", "BATTEN", "BC_RESTRAINT", "DIAG_BRACE", "COLUMN", "STRAP", "HIP_RAFTER", "STRINGER", "TREAD", "LEDGER", "TANK_BEAM"}


def in_cut(voids, x, z) -> bool:
    return any(v[0] < x < v[1] and v[2] < z < v[3] for v in voids)


def cov(ms, x, z) -> bool:
    return any(m.x0 - 0.5 <= x <= m.x1 + 0.5 and m.z0 - 0.5 <= z <= m.z1 + 0.5 for m in ms)


def validate(ctx: Ctx) -> None:
    by_parent = defaultdict(list)
    for m in ctx.members:
        by_parent[m.parent].append(m)
    panels = {p.id: p for p in ctx.panels}

    # --- por painel: espaçamento, interferência, apoio das placas
    for pid, p in panels.items():
        ms = by_parent[pid]
        core = [m for m in ms if m.plane == "core" and m.orientation in ("V", "H")]
        for i, a in enumerate(core):
            for b in core[i + 1:]:
                if contact(a, b)[0] == "clash":
                    ctx.issue("V-061", "error", pid, f"interferência entre {a.id} e {b.id}")
        z0s, z1s, smax = ctx.panel_bands[pid]
        ros = ctx.panel_ros[pid]
        verts = [m for m in core if m.orientation == "V" and m.role in VERTICAL]
        zs = [z0s + 5, (z0s + z1s) / 2, z1s - 5] + [(r[2] + r[3]) / 2 for r in ros] + \
             [max(z0s + 5, r[2] / 2) for r in ros] + [(r[3] + z1s) / 2 for r in ros]
        for z in zs:
            row = sorted([m for m in verts if m.z0 - 0.1 <= z <= m.z1 + 0.1], key=lambda m: m.x0)
            for a, b in zip(row, row[1:]):
                mid = ((a.x0 + a.x1) / 2 + (b.x0 + b.x1) / 2) / 2
                if any(r[0] < mid < r[1] and r[2] < z < r[3] for r in ros):
                    continue
                if any(h.orientation == "H" and h.role in ("HEADER", "SILL", "PACKER") and h.x0 <= mid <= h.x1
                       and h.z0 - 1 <= z <= h.z1 + 1 for h in core):
                    continue
                d = (b.x0 + b.x1) / 2 - (a.x0 + a.x1) / 2
                if d > smax + 0.5:
                    ctx.issue("V-006", "error", pid, f"espaçamento de {d:.0f} mm entre {a.id} e {b.id} (máx. {smax:.0f})")
        # apoio das juntas de placas (V-062)
        voids = [(r[0], r[1], r[2], r[3]) for r in ros]
        for sid in p.sheet_ids:
            sh = next(s for s in ctx.sheets if s.id == sid)
            edges_v = [e for e in (sh.x0, sh.x1) if 1 < e < p.length - 1]
            for e in edges_v:
                z = sh.z0 + 50
                while z < sh.z1 - 49:
                    if not any(c[0] - 1 <= e <= c[1] + 1 and c[2] - 1 <= z <= c[3] + 1 for c in sh.cutouts):
                        if not all(cov(core, xp, z) or in_cut(voids, xp, z) for xp in (e - 9, e + 9)):
                            ctx.issue("V-062", "error", sid, f"junta vertical em x={e:.0f}, z={z:.0f} sem apoio")
                            break
                    z += 300
            edges_h = [e for e in (sh.z0, sh.z1) if 1 < e < p.height - 1]
            for e in edges_h:
                x = sh.x0 + 50
                while x < sh.x1 - 49:
                    if not any(c[0] - 1 <= x <= c[1] + 1 and c[2] - 1 <= e <= c[3] + 1 for c in sh.cutouts):
                        if not all(cov(core, x, zp) or in_cut(voids, x, zp) for zp in (e - 9, e + 9)):
                            ctx.issue("V-062", "error", sid, f"junta horizontal em z={e:.0f}, x={x:.0f} sem apoio")
                            break
                    x += 150

    # --- vão aleatório entre peças (V-074): nenhuma folga entre 2,5 mm e 60 mm
    groups = defaultdict(list)
    for m in ctx.members:
        if m.plane == "core" and m.orientation in ("V", "H") and m.frame in ("panel", "plan") and m.group in ("wall", "floor"):
            groups[m.parent].append(m)
    for pid, ms in groups.items():
        found = 0
        for i, a in enumerate(ms):
            for b in ms[i + 1:]:
                gx = max(a.x0, b.x0) - min(a.x1, b.x1)
                gz = max(a.z0, b.z0) - min(a.z1, b.z1)
                if TOUCH < gx < MIN_CLEAR and gz < -1:
                    kind = "lado a lado"
                    gap = (min(a.x1, b.x1), max(a.x0, b.x0), max(a.z0, b.z0), min(a.z1, b.z1))
                elif TOUCH < gz < MIN_CLEAR and gx < -1:
                    kind = "topo"
                    gap = (max(a.x0, b.x0), min(a.x1, b.x1), min(a.z1, b.z1), max(a.z0, b.z0))
                else:
                    continue
                gx0, gx1, gz0, gz1 = gap
                # só é vão se o espaço entre as duas peças estiver vazio (sem outra peça no meio)
                if any(c is not a and c is not b and c.x0 < gx1 - 0.5 and c.x1 > gx0 + 0.5 and c.z0 < gz1 - 0.5
                       and c.z1 > gz0 + 0.5 for c in ms):
                    continue
                found += 1
                if found <= 5:
                    ctx.issue("V-074", "error", pid, f"vão de {max(gx, gz):.1f} mm ({kind}) entre {a.id} e {b.id}")

    # --- peça pequena demais para fabricar (remendo): menor que 60 mm no comprimento
    for m in ctx.members:
        if m.group in ("wall", "floor") and m.plane == "core" and m.role in ("BLOCK", "BRIDGING", "NAILER") \
                and 0 < m.cut_length < MIN_CLEAR - 0.5:
            ctx.issue("V-074", "error", m.parent, f"{m.id} com {m.cut_length:.0f} mm: peça pequena demais (remendo em vão)")

    # --- encontros entre paredes em planta (V-075): sem sobreposição e sem folga
    from shapely.geometry import Polygon as SPoly
    bands = {}
    for wid, wf in ctx.wall_frames.items():
        u, d = wf.dirv, wf.depth
        n = (-u[1] * d / 2, u[0] * d / 2)
        a, b = wf.origin, wf.to_global(wf.L)
        poly = SPoly([g.add(a, n), g.add(b, n), g.sub(b, n), g.sub(a, n)])
        mid = wf.to_global(wf.L / 2)
        for info in (wf.junc.start, wf.junc.end):
            if info.clip:
                I, O = info.clip
                dvec = g.unit(g.sub(O, I))
                big = 1e5
                p1, p2 = g.sub(I, g.mul(dvec, big)), g.add(I, g.mul(dvec, big))
                nn = (-dvec[1], dvec[0])
                side = 1 if g.dot(g.sub(mid, I), nn) > 0 else -1
                hp = SPoly([p1, p2, g.add(p2, g.mul(nn, side * big)), g.add(p1, g.mul(nn, side * big))])
                poly = poly.intersection(hp)
        bands[wid] = poly
    ids = sorted(bands)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if ctx.wall_frames[a].wall.level != ctx.wall_frames[b].wall.level:
                continue
            ov = bands[a].intersection(bands[b]).area
            if ov > 1.0:
                ctx.issue("V-075", "error", f"{a}+{b}", f"paredes se sobrepõem {ov:.0f} mm² em planta")
    for wid, wf in ctx.wall_frames.items():
        for end, info in (("start", wf.junc.start), ("end", wf.junc.end)):
            if info.kind == "free":             # ponta solta perto de outra parede = vão entre paredes
                from shapely.geometry import Point as SPt
                pt = SPt(wf.wall.start if end == "start" else wf.wall.end)
                for oid, band in bands.items():
                    if oid == wid or ctx.wall_frames[oid].wall.level != wf.wall.level:
                        continue
                    dd = band.distance(pt) - wf.depth * 0  # distância do eixo da ponta à face da outra parede
                    if 0.5 < dd < 300:
                        ctx.issue("V-075", "error", f"{wid}+{oid}",
                                  f"ponta da parede a {dd:.0f} mm de {oid} sem encostar: ajuste o desenho (encontro ou folga ≥ 300 mm)")
            if info.kind in ("through", "butt", "tee", "miter", "inline") and info.other in bands:
                dgap = bands[wid].distance(bands[info.other])
                if dgap > 0.5:
                    ctx.issue("V-075", "error", f"{wid}+{info.other}", f"folga de {dgap:.1f} mm entre as paredes no encontro")

    # --- conectividade (V-057 / V-058)
    deg = defaultdict(int)
    for c in ctx.connections:
        deg[c.a] += 1
        deg[c.b] += 1
        if (c.fastener in ("definir", "", None) or c.qty <= 0) and c.type != "LG-07":
            ctx.issue("V-058", "error", c.id, f"ligação {c.type} sem fixador/quantidade definidos")
    for m in ctx.members:
        if m.role in DEGREE_EXEMPT or m.frame == "wall":
            continue
        need = 1 if m.role in ("ARCH_FILLER", "PACKER") else 2
        if deg[m.id] < need:
            ctx.issue("V-057", "error", m.id, f"peça com {deg[m.id]} ligação(ões) (mínimo {need})")

    # --- corte completo e barra comercial (V-063 / V-064)
    for m in ctx.members:
        if m.role in LINEAR_EXEMPT or m.special:
            continue
        if m.cut_length <= 0:
            ctx.issue("V-064", "error", m.id, "peça sem comprimento de corte")
            continue
        stock = ctx.cat.stock_lengths(m.item)
        if stock and m.cut_length > max(stock) + 0.5:
            ctx.issue("V-063", "error", m.id, f"{m.cut_length:.0f} mm maior que a barra de {max(stock):.0f} mm")

    # --- contraventamento por eixo e pavimento (V-017)
    Bm = ctx.rules.data["bracing"]["min_effective_length"]
    tot = defaultdict(float)
    for lvl, ax, L, _ in ctx.braced_segments:
        tot[(lvl, ax)] += L
    project_levels = {l.id for l in ctx.project.levels}      # complementos (mureta/parede alta) não entram
    levels_with_walls = {wf.wall.level for wf in ctx.wall_frames.values()} & project_levels
    for lvl in sorted(levels_with_walls):
        for ax in ("x", "y"):
            need = Bm.get(f"{lvl}_{ax}", Bm["default"])
            have = tot[(lvl, ax)]
            if have < need:
                ctx.issue("V-017", "error", f"{lvl}/{ax}", f"contraventamento {have:.0f} mm < mínimo {need} mm")
            else:
                ctx.issue("V-000", "info", f"{lvl}/{ax}", f"contraventamento efetivo {have:.0f} mm (mín. {need})")

    # --- alinhamento em linha (V-004, obrigatório em aço)
    if ctx.system == "steel":
        tol = ctx.rules.data.get("in_line_tolerance", 20)
        # apoios no nível das paredes (treliças no mesmo nível; vigas de piso no nível de baixo)
        levels = sorted(ctx.project.levels, key=lambda l: l.elevation)
        below = {levels[i + 1].id: levels[i].id for i in range(len(levels) - 1)}
        checked = over_header = 0
        for kind, eid, pt, lvl in ctx.bearing_points:
            wl = lvl if kind in ("truss", "column") else below.get(lvl)
            for wf in ctx.wall_frames.values():
                if wf.wall.level != wl or not wf.wall.bearing:
                    continue
                t_, perp = g.project_param(pt, wf.origin, wf.to_global(wf.L))
                if perp > wf.depth / 2 + 5 or not (0 <= t_ <= wf.L):
                    continue
                if any(of.zone_l <= t_ <= of.zone_r for of in wf.openings):
                    over_header += 1          # apoio sobre verga: a verga distribui a carga
                    continue
                corner = wf.junc.start.other_depth + wf.t if wf.junc.start.kind == "through" else 0
                corner_e = wf.junc.end.other_depth + wf.t if wf.junc.end.kind == "through" else 0
                if t_ < corner or t_ > wf.L - corner_e:
                    continue                  # treliça de oitão: apoia na parede de topo
                checked += 1
                dmin = min((abs(c - t_) for c in wf.stud_centers), default=1e9)
                if dmin > tol:
                    ctx.issue("V-004", "error", eid, f"apoio fora do alinhamento com montante de {wf.wall.id} "
                                                     f"({dmin:.0f} mm, tol. {tol})")
        ctx.issue("V-000", "info", "in-line", f"{checked} apoios alinhados a montantes conferidos; {over_header} sobre vergas")

    # --- caminho de carga vertical (V-024)
    levels = sorted(ctx.project.levels, key=lambda l: l.elevation)
    for i, lv in enumerate(levels[1:], start=1):
        below_walls = [wf for wf in ctx.wall_frames.values() if wf.wall.level == levels[i - 1].id]
        for wf in [w for w in ctx.wall_frames.values() if w.wall.level == lv.id and w.wall.bearing]:
            mid = wf.to_global(wf.L / 2)
            ok = False
            for b in below_walls:
                t_, perp = g.project_param(mid, b.origin, b.to_global(b.L))
                if perp <= b.depth / 2 and 0 <= t_ <= b.L and abs(g.dot(wf.dirv, b.dirv)) > 0.99:
                    ok = True
            if not ok:
                ctx.issue("V-024", "warning", wf.wall.id, "parede portante sem parede alinhada abaixo: "
                                                          "carga vai para as vigas de piso, confirmar com o engenheiro")

    # --- aprovação (A10.7)
    if not ctx.rules.approved():
        ctx.issue("V-000", "info", ctx.rules.name,
                  "RASCUNHO: ruleset sem aprovação do engenheiro. Pendentes: " + ", ".join(ctx.rules.unapproved_rules()))
    used = sorted({m.item for m in ctx.members} | {h.item for h in ctx.hardware} | {s.item for s in ctx.sheets})
    na = [i for i in used if i in ctx.cat.items and not ctx.cat.is_approved(i)]
    if na:
        ctx.issue("V-011", "warning", "catálogo", f"{len(na)} itens usados sem aprovação: " + ", ".join(na))
