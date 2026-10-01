"""Caixa d'água no ático (padrão Vigora).

A caixa é uma INTENÇÃO no projeto (modelo + posição). Tudo em volta é derivado a cada geração:
  1. posição: dada ou automática (centro entre duas paredes portantes paralelas, na interseção com uma
     parede interna portante perpendicular quando existir);
  2. apoio desacoplado da cobertura: vigas duplas (2 x 38 x 235) entre as duas paredes portantes (vão livre
     <= 1,50 m), colocadas nos vãos entre as treliças (nunca sobre banzos) + deck de OSB;
  3. envelope de colisão: cilindro da bacia (diâmetro da bacia) do deck até a tampa + 0,50 m;
  4. o telhado lê o envelope e transforma as treliças que o cruzam em treliças de ático (engine/roofs.py);
  5. validações: apoio (V-091), vão da viga (V-092), altura sob o telhado (V-090), colisão 3D (V-093).
Adicionar, mover, trocar o modelo ou remover a caixa = mudar o JSON e gerar de novo.
"""
from __future__ import annotations

import math
from pathlib import Path

import yaml

from ..model import Sheet, TankSpec
from .context import Ctx

ROOT = Path(__file__).resolve().parents[3]


def load_tank_catalog(root: Path = ROOT) -> dict:
    return yaml.safe_load((root / "catalog" / "tanks.yaml").read_text(encoding="utf-8"))


def _roof_for(ctx: Ctx, level: str, pt=None):
    roofs = [r for r in ctx.project.roofs if r.level == level]
    if pt is not None:
        for r in roofs:
            if r.outline:
                xs = [q[0] for q in r.outline]
                ys = [q[1] for q in r.outline]
                if min(xs) <= pt[0] <= max(xs) and min(ys) <= pt[1] <= max(ys):
                    return r
    return roofs[0] if roofs else None


def _roof_frame(ctx: Ctx, rs):
    """(o_along, Lr, o_span, span) do telhado a partir do contorno ou das paredes externas."""
    if rs.outline:
        xs = [q[0] for q in rs.outline]
        ys = [q[1] for q in rs.outline]
    else:
        pts = []
        for wf in ctx.wall_frames.values():
            if wf.wall.level != rs.level or not wf.wall.exterior:
                continue
            n = (-wf.dirv[1] * wf.depth / 2, wf.dirv[0] * wf.depth / 2)
            for q in (wf.origin, wf.to_global(wf.L)):
                pts += [(q[0] + n[0], q[1] + n[1]), (q[0] - n[0], q[1] - n[1])]
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
    if rs.ridge_axis == "x":
        return min(xs), max(xs) - min(xs), min(ys), max(ys) - min(ys)
    return min(ys), max(ys) - min(ys), min(xs), max(xs) - min(xs)


def _underside_estimate(ctx: Ctx, rs, span_coord: float, span: float) -> float:
    """Altura aproximada (acima do banzo inferior) da face inferior do banzo superior no ponto do vão."""
    from .roofs import choose_type
    row = choose_type(rs, span, ctx) or {"top": "W-38x140", "bottom": "W-38x140"}
    tan = math.tan(math.radians(rs.pitch_deg))
    cos = math.cos(math.radians(rs.pitch_deg))
    db, dt = ctx.cat.depth(row["bottom"]), ctx.cat.depth(row["top"])
    if rs.kind == "mono":
        s = (span - span_coord) if rs.high_side == "start" else span_coord
    else:
        s = min(span_coord, span - span_coord)
    return db + dt / cos + s * tan - dt / cos


def plan_tanks(ctx: Ctx, levels: list) -> None:
    if not ctx.project.tanks:
        return
    cat = load_tank_catalog()
    presets = cat["water_tank_presets"]
    SR = cat["support_rules"]
    lv = {l.id: l for l in levels}
    for ts in ctx.project.tanks:
        tid = f"{ctx.pfx}-{ts.level}-{ts.id}"
        pre = presets.get(ts.model)
        if pre is None:
            ctx.issue("V-094", "error", tid, f"modelo de caixa '{ts.model}' fora do catálogo ({', '.join(presets)})")
            continue
        if ts.installation != "attic":
            ctx.issue("V-094", "error", tid, "instalação em torre ainda não suportada (padrão Vigora: ático)")
            continue
        rs = _roof_for(ctx, ts.level, ts.position)
        if rs is None:
            ctx.issue("V-094", "error", tid, "caixa no ático sem telhado no nível")
            continue
        o_al, Lr, o_sp, span = _roof_frame(ctx, rs)
        ax = rs.ridge_axis                               # paredes de apoio correm paralelas à cumeeira
        R_tray = pre["tray_diameter_m"] * 500.0
        env_h = (pre["tank_height_m"] + pre["maintenance_clearance_top_m"]) * 1000.0
        beam_d = ctx.cat.depth(SR["beam_item"])
        deck_t = ctx.cat.get(SR["deck_item"])["thickness"]

        # pares de paredes portantes paralelas à cumeeira com vão livre <= 1,50 m (banheiro, shaft, hall)
        cand = [wf for wf in ctx.wall_frames.values() if wf.wall.level == ts.level and wf.wall.bearing
                and wf.axis == ax]

        def coord(wf):
            return wf.origin[1] if ax == "x" else wf.origin[0]

        def extent(wf):
            a, b = (wf.origin[0], wf.to_global(wf.L)[0]) if ax == "x" else (wf.origin[1], wf.to_global(wf.L)[1])
            return min(a, b), max(a, b)
        pairs = []
        for i, a in enumerate(cand):
            for b in cand[i + 1:]:
                w1, w2 = (a, b) if coord(a) < coord(b) else (b, a)
                clear = coord(w2) - coord(w1) - (w1.depth + w2.depth) / 2
                lo = max(extent(w1)[0], extent(w2)[0])
                hi = min(extent(w1)[1], extent(w2)[1])
                if 300 <= clear <= SR["beam_max_span_mm"] + 0.5 and hi - lo >= 2 * R_tray * 0.6:
                    pairs.append((w1, w2, clear, lo, hi))
        perp = [wf for wf in ctx.wall_frames.values() if wf.wall.level == ts.level and wf.wall.bearing
                and not wf.wall.exterior and wf.axis != ax]

        def center_for(pair):
            w1, w2, clear, lo, hi = pair
            mid_s = (coord(w1) + coord(w2)) / 2
            xs = []
            for pw in perp:                         # cenário A: interseção com parede portante perpendicular
                c = pw.origin[0] if ax == "x" else pw.origin[1]
                e0, e1 = sorted((pw.origin[1], pw.to_global(pw.L)[1]) if ax == "x" else (pw.origin[0], pw.to_global(pw.L)[0]))
                crosses = e0 <= coord(w2) + w2.depth / 2 + 5 and e1 >= coord(w1) - w1.depth / 2 - 5
                if crosses and lo + R_tray * 0.6 <= c <= hi - R_tray * 0.6:
                    xs.append((c, "A"))
            if not xs:
                xs.append(((lo + hi) / 2, "B"))
            return [(x_, mid_s, sc) for x_, sc in xs]

        def margin(al, sp_):                        # folga do envelope sob o telhado (mm, estimada)
            deck_top = beam_d + deck_t
            worst = 1e9
            for k in range(-4, 5):
                s_ = sp_ - o_sp + k * R_tray / 4
                if 0 < s_ < span:
                    worst = min(worst, _underside_estimate(ctx, rs, s_, span) - deck_top - env_h)
            return worst

        chosen = None
        if ts.position is not None:
            X, Y = ts.position
            al, sp_ = (X, Y) if ax == "x" else (Y, X)
            for pair in sorted(pairs, key=lambda p: p[2]):
                w1, w2, clear, lo, hi = pair
                if coord(w1) < sp_ < coord(w2) and lo - 1 <= al <= hi + 1:
                    chosen = (pair, al, sp_, "manual")
                    break
            if chosen is None:
                ctx.issue("V-091", "error", tid,
                          f"posição ({X:.0f}, {Y:.0f}) sem duas paredes portantes paralelas com vão livre até "
                          f"{SR['beam_max_span_mm']} mm embaixo; use \"position\": null para a sugestão automática")
                continue
        else:
            opts = []
            for pair in pairs:
                for al, sp_, sc in center_for(pair):
                    opts.append((margin(al, sp_) >= 0, sc == "A", margin(al, sp_), -abs(sp_ - (o_sp + span / 2)),
                                 pair, al, sp_, sc))
            if not opts:
                ctx.issue("V-091", "error", tid, "nenhum par de paredes portantes paralelas (vão livre até "
                                                 f"{SR['beam_max_span_mm']} mm) para apoiar a caixa: crie um shaft/hall "
                                                 "portante ou informe a posição")
                continue
            best = max(opts, key=lambda o: (o[0], o[1], o[3], o[2]))
            chosen = (best[4], best[5], best[6], "auto-" + best[7])
        pair, al, sp_, how = chosen
        w1, w2, clear, lo, hi = pair
        X, Y = (al, sp_) if ax == "x" else (sp_, al)
        if abs(w1.H - w2.H) > 1:
            ctx.issue("V-091", "error", tid, f"paredes de apoio com alturas diferentes ({w1.wall.id}, {w2.wall.id})")
        z_wall = lv[ts.level].elevation + w1.H
        # vigas duplas nos vãos entre treliças (grade global da cobertura)
        sp_tr = rs.spacing or ctx.rules.data["roof"]["spacing"]
        t_tr = ctx.cat.face("W-38x140")
        k0 = math.floor((al - R_tray) / sp_tr) - 1
        beam_w = ctx.cat.face(SR["beam_item"]) * SR["beam_plies"]
        beams = []
        for k in range(k0, k0 + int(2 * R_tray / sp_tr) + 4):
            bay0, bay1 = k * sp_tr + t_tr / 2, (k + 1) * sp_tr - t_tr / 2       # vão livre entre banzos
            if bay1 - bay0 >= 2 * beam_w + 3 * 60:          # duas vigas por vão, 60 mm livres dos banzos
                cands = [bay0 + 60 + beam_w / 2, bay1 - 60 - beam_w / 2]
            else:
                cands = [(bay0 + bay1) / 2]
            for c in cands:
                if al - R_tray + 60 <= c <= al + R_tray - 60 and lo + beam_w <= c <= hi - beam_w:
                    beams.append(c)
        if len(beams) < 2:
            ctx.issue("V-091", "error", tid, "menos de 2 vigas de apoio cabem sob a bacia entre as treliças")
            continue
        s0 = coord(w1) - w1.depth / 2
        s1 = coord(w2) + w2.depth / 2
        span_beam = coord(w2) - coord(w1) - (w1.depth + w2.depth) / 2
        if span_beam > SR["beam_max_span_mm"] + 0.5:
            ctx.issue("V-092", "error", tid, f"vão livre da viga {span_beam:.0f} mm > {SR['beam_max_span_mm']} mm")
        load = pre["weight_full_kn"]
        ctx.placements[tid] = {"z": z_wall, "depth": beam_d}
        for i, c in enumerate(beams, 1):
            a0, a1 = c - beam_w / 2, c + beam_w / 2
            x0, x1, y0, y1 = (a0, a1, s0, s1) if ax == "x" else (s0, s1, a0, a1)
            m = ctx.new_member("TANK_BEAM", SR["beam_item"], ts.level, "tank", tid, frame="plan", x0=x0, x1=x1,
                               z0=y0, z1=y1, orientation="H", plies=SR["beam_plies"], cut_length=round(s1 - s0, 1),
                               depth=beam_d, rule="tanks.support",
                               note=f"viga dupla da caixa {ts.model}: vão livre {span_beam:.0f} mm entre "
                                    f"{w1.wall.id} e {w2.wall.id}; {load / len(beams):.1f} kN por viga")
            m.id = f"{tid}-TANK_BEAM-{i:02d}"
            ctx.members.append(m)
        # deck de OSB (placa com a bacia em cima)
        half = R_tray
        dx0, dx1 = (al - half, al + half)
        ds0, ds1 = min(s0, sp_ - half), max(s1, sp_ + half)
        if (s0 - (sp_ - half)) > 150 or ((sp_ + half) - s1) > 150:
            ctx.issue("V-091", "warning", tid, "deck em balanço de mais de 150 mm além das paredes de apoio")
        xs0, xs1, ys0, ys1 = (dx0, dx1, ds0, ds1) if ax == "x" else (ds0, ds1, dx0, dx1)
        ctx.sheets.append(Sheet(id=f"{tid}-DECK-01", item=SR["deck_item"], parent=tid, x0=round(xs0, 1),
                                x1=round(xs1, 1), z0=round(ys0, 1), z1=round(ys1, 1),
                                area_m2=round((xs1 - xs0) * (ys1 - ys0) / 1e6, 3)))
        deck_top = z_wall + beam_d + deck_t
        ctx.tank_zones.append({"id": tid, "level": ts.level, "roof": rs.id, "center": (X, Y), "R": R_tray,
                               "z0": deck_top, "z1": deck_top + env_h, "axis": ax})
        # compras: caixa, bacia, ladrão da bacia até o beiral mais próximo, fixação das vigas
        ctx.hw(f"CAIXA-{ts.model}", 1, f"{tid} caixa {pre['capacity_liters']} L ({pre['brand']})")
        ctx.hw(f"BACIA-CONTENCAO-{int(round(pre['tray_diameter_m'] * 1000))}", 1, f"{tid} bacia estanque")
        d_eave = min(sp_ - o_sp, o_sp + span - sp_) if rs.kind != "mono" else \
            ((sp_ - o_sp) if rs.high_side == "end" else (o_sp + span - sp_))
        ctx.hw(SR["overflow_pipe"], round((d_eave + 1000) / 1000, 1), f"{tid} ladrão da bacia Ø32 até o beiral", unit="m")
        ctx.hw("CONECTOR-ARRANC-H1", 2 * len(beams), f"{tid} fixação das vigas nos frechais")
        ctx.tanks.append({"id": tid, "model": ts.model, "level": ts.level, "center": [X, Y], "how": how,
                          "supports": [w1.wall.id, w2.wall.id], "span_beam": span_beam, "beams": len(beams),
                          "z_wall": z_wall, "deck_top": deck_top, "R_tray": R_tray,
                          "tank_d": pre["tank_diameter_m"] * 1000, "tank_h": pre["tank_height_m"] * 1000,
                          "tray_h": pre["tray_height_m"] * 1000, "env_top": deck_top + env_h,
                          "capacity": pre["capacity_liters"], "load_kn": load, "axis": ax})
        ctx.issue("V-000", "info", tid, f"caixa {pre['capacity_liters']} L em ({X:.0f}, {Y:.0f}) "
                                        f"[{'automática' if how.startswith('auto') else 'manual'}"
                                        f"{', interseção de paredes' if how.endswith('A') else ''}]: vigas 2×38×235 entre "
                                        f"{w1.wall.id} e {w2.wall.id} (vão livre {span_beam:.0f} mm)")


def check_tank_clashes(res) -> list:
    """Colisão 3D do envelope da caixa (bacia + tampa + 0,50 m) com qualquer peça do modelo."""
    from shapely.geometry import MultiPoint, Point, Polygon

    from ..model import Issue
    from ..revit_bridge import revit_solids
    issues = []
    tanks = res.stats.get("tanks", [])
    if not tanks:
        return issues
    pl = res.stats["placements"]
    by_id = {m.id: m for m in res.members}
    for t in tanks:
        cx, cy = t["center"]
        R, z0, z1 = t["R_tray"], t["deck_top"] + 1, t["env_top"]
        circ = Point(cx, cy).buffer(R, 32)
        hits = []
        for sol in revit_solids(res)["solids"]:
            if sol["group"] == "tank":
                continue
            m = by_id.get(sol["id"])
            if m is not None and m.frame == "truss" and m.parent in pl:
                o, sd = pl[m.parent]["origin"], pl[m.parent]["span_dir"]
                along = (-sd[1], sd[0])
                plane = o[0] * along[0] + o[1] * along[1]
                c_al = cx * along[0] + cy * along[1]
                th = abs(sol["extrude"][0] * along[0] + sol["extrude"][1] * along[1]) or 38.0
                dd = max(abs(plane - c_al) - th / 2, 0.0) if abs(plane - c_al) > th / 2 else 0.0
                if dd >= R:
                    continue
                w = (R * R - dd * dd) ** 0.5
                cs = (cx - o[0]) * sd[0] + (cy - o[1]) * sd[1]
                rect = Polygon([(cs - w, z0 - o[2]), (cs + w, z0 - o[2]), (cs + w, z1 - o[2]), (cs - w, z1 - o[2])])
                if Polygon(m.polygon).intersection(rect).area > 1.0:
                    hits.append(sol["id"])
                continue
            pts = sol["profile"] + [[p[0] + sol["extrude"][0], p[1] + sol["extrude"][1], p[2] + sol["extrude"][2]]
                                    for p in sol["profile"]]
            zs0, zs1 = min(p[2] for p in pts), max(p[2] for p in pts)
            if zs1 <= z0 or zs0 >= z1:
                continue
            hull = MultiPoint([(p[0], p[1]) for p in pts]).convex_hull
            if hull.intersection(circ).area > 1.0:
                hits.append(sol["id"])
        for h in hits[:8]:
            issues.append(Issue(code="V-093", severity="error", element=t["id"],
                                message=f"colisão da caixa (envelope com bacia e +0,50 m) com {h}"))
        if not hits:
            issues.append(Issue(code="V-000", severity="info", element=t["id"],
                                message="caixa d'água sem colisão com nenhuma peça (envelope completo livre)"))
    return issues
