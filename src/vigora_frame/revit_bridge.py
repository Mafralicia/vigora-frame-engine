"""Ponte para o Revit (seção 11): peças -> sólidos 3D em coordenadas globais (mm).

Cada sólido é um perfil plano (polígono 3D) extrudado por um vetor. O script do
pyRevit só converte mm -> pés e cria um DirectShape por peça. Assim toda a
geometria fica testável fora do Revit.
"""
from __future__ import annotations

import hashlib
import json

from .model import Result


def _v(a, b, k=1.0):
    return [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k]


def _sig(profile, ext, item):
    return hashlib.sha1(json.dumps([[round(c, 1) for c in p] for p in profile] + [[round(c, 1) for c in ext], item])
                        .encode()).hexdigest()[:12]


def _clip_poly(pn, x0, x1, dep):
    """Planta da peça (faixa x0..x1 na espessura) cortada pelas retas de meia-esquadria do painel."""
    from shapely.geometry import Polygon
    o, d = pn.origin, pn.direction
    nrm = (-d[1], d[0])
    pts = [(o[0] + d[0] * x + nrm[0] * k, o[1] + d[1] * x + nrm[1] * k) for x, k in
           ((x0, -dep / 2), (x1, -dep / 2), (x1, dep / 2), (x0, dep / 2))]
    poly = Polygon(pts)
    mid = (o[0] + d[0] * pn.length / 2, o[1] + d[1] * pn.length / 2)
    for clip in (pn.clip_start, pn.clip_end):
        if not clip:
            continue
        (ix, iy), (ox, oy) = clip
        dx, dy = ox - ix, oy - iy
        L = (dx * dx + dy * dy) ** 0.5
        dx, dy = dx / L, dy / L
        nx, ny = -dy, dx
        side = 1 if (mid[0] - ix) * nx + (mid[1] - iy) * ny > 0 else -1
        B = 1e5
        hp = Polygon([(ix - dx * B, iy - dy * B), (ix + dx * B, iy + dy * B),
                      (ix + dx * B + nx * side * B, iy + dy * B + ny * side * B),
                      (ix - dx * B + nx * side * B, iy - dy * B + ny * side * B)])
        poly = poly.intersection(hp)
    return poly


def revit_solids(res: Result) -> dict:
    panels = {p.id: p for p in res.panels}
    walls = {}
    for p in res.panels:
        wid = p.id.rsplit("-PN", 1)[0]
        if wid not in walls:
            walls[wid] = ((p.origin[0] - p.direction[0] * p.x_start, p.origin[1] - p.direction[1] * p.x_start,
                           p.origin[2]), p.direction)
    wall_depth = {}
    for m in res.members:
        if m.role == "STUD_END":
            wall_depth[m.parent] = m.depth
            wall_depth[m.parent.rsplit("-PN", 1)[0]] = m.depth
    pl = res.stats.get("placements", {})
    levels = res.stats.get("levels", {})
    out = []
    for m in res.members:
        prof, ext = None, None
        pn_ = panels.get(m.parent)
        if (m.frame == "panel" and pn_ is not None and (pn_.clip_start or pn_.clip_end) and m.plane == "core"
                and not m.polygon and m.orientation in ("V", "H")):
            dep = wall_depth.get(m.parent, m.depth or 89.0)
            poly = _clip_poly(pn_, m.x0, m.x1, dep)
            if poly.is_empty or poly.area < 1:
                continue
            z0 = pn_.origin[2] + m.z0
            prof = [[x, y, z0] for x, y in list(poly.exterior.coords)[:-1]]
            ext = [0.0, 0.0, max(m.z1 - m.z0, 1.0)]
        elif m.frame in ("panel", "wall"):
            if m.frame == "panel":
                pn = panels[m.parent]
                o, d = pn.origin, pn.direction
            else:
                if m.parent not in walls:
                    continue
                o, d = walls[m.parent]
            u = [d[0], d[1], 0.0]
            n = [-d[1], d[0], 0.0]
            dep = wall_depth.get(m.parent, m.depth or 89.0)
            if m.plane == "face":          # fitas na face externa
                base = _v(list(o), n, -dep / 2 - 1)
                thick = 1.0
            elif m.role in ("HEADER", "PACKER", "ARCH_FILLER"):
                thick = min(dep, 38.0 * m.plies) if m.role == "HEADER" else dep
                base = _v(list(o), n, -thick / 2)
            else:
                base = _v(list(o), n, -dep / 2)
                thick = dep
            pts = m.polygon or [(m.x0, m.z0), (m.x1, m.z0), (m.x1, max(m.z1, m.z0 + 1)), (m.x0, max(m.z1, m.z0 + 1))]
            prof = [[base[0] + u[0] * x, base[1] + u[1] * x, base[2] + z] for x, z in pts]
            ext = [n[0] * thick, n[1] * thick, 0.0]
        elif m.frame == "truss" and m.parent in pl:
            o, sd = pl[m.parent]["origin"], pl[m.parent]["span_dir"]
            along = [sd[1], -sd[0], 0.0] if sd[0] == 0 else [0.0, 1.0, 0.0]
            t = m.depth or 38.0
            base = _v(list(o), along, -t / 2)
            prof = [[base[0] + sd[0] * x, base[1] + sd[1] * x, base[2] + y] for x, y in m.polygon]
            ext = [along[0] * t, along[1] * t, 0.0]
        elif m.frame == "stair" and m.id in pl:
            P_ = pl[m.id]
            o, sd = P_["origin"], P_["span_dir"]
            ac = (-sd[1], sd[0])
            base = [o[0] + ac[0] * P_["off"], o[1] + ac[1] * P_["off"], o[2]]
            prof = [[base[0] + sd[0] * x, base[1] + sd[1] * x, base[2] + z] for x, z in m.polygon]
            ext = [ac[0] * P_["thick"], ac[1] * P_["thick"], 0.0]
        elif m.frame == "plan" and m.group in ("floor", "tank") and m.parent in pl:
            z = pl[m.parent]["z"]
            prof = [[m.x0, m.z0, z], [m.x1, m.z0, z], [m.x1, m.z1, z], [m.x0, m.z1, z]]
            ext = [0.0, 0.0, m.depth or 235.0]
        elif m.role == "COLUMN":
            z = levels.get(m.level, {}).get("elevation", 0.0)
            h = 70.0
            prof = [[m.x0 - h, m.z0 - h, z], [m.x0 + h, m.z0 - h, z], [m.x0 + h, m.z0 + h, z], [m.x0 - h, m.z0 + h, z]]
            ext = [0.0, 0.0, m.cut_length]
        if prof is None:
            continue                       # acessórios sem posição (ripas, travamentos de cobertura)
        prof = [[round(c, 2) for c in p] for p in prof]
        ext = [round(c, 3) for c in ext]
        out.append({"id": m.id, "role": m.role, "item": m.item, "group": m.group, "parent": m.parent,
                    "level": m.level, "cut_length": m.cut_length, "profile": prof, "extrude": ext,
                    "sig": _sig(prof, ext, m.item)})
    out += tank_solids(res)
    return {"project": res.project, "run_id": res.run_id, "approved": res.ruleset_approved, "units": "mm",
            "solids": out}


def tank_solids(res: Result) -> list:
    """Caixa d'água, bacia e deck como sólidos (cilindros de 32 lados) para o 3D e o Revit."""
    import math
    out = []
    for t in res.stats.get("tanks", []):
        cx, cy = t["center"]
        z = t["deck_top"]
        for role, r_, h_, z0 in (("TANK_TRAY", t["R_tray"], t["tray_h"], z), ("WATER_TANK", t["tank_d"] / 2, t["tank_h"], z + 5)):
            prof = [[round(cx + r_ * math.cos(2 * math.pi * k / 32), 2), round(cy + r_ * math.sin(2 * math.pi * k / 32), 2),
                     round(z0, 2)] for k in range(32)]
            ext_ = [0.0, 0.0, round(h_, 2)]
            item_ = f"CAIXA-{t['model']}" if role == "WATER_TANK" else "BACIA"
            out.append({"id": f"{t['id']}-{role}", "role": role, "item": item_, "group": "tank", "parent": t["id"],
                        "level": t["level"], "cut_length": 0.0, "profile": prof, "extrude": ext_,
                        "sig": _sig(prof, ext_, item_)})
        for sh in res.sheets:
            if sh.parent == t["id"]:
                zz = t["deck_top"] - 18.3
                prof = [[sh.x0, sh.z0, zz], [sh.x1, sh.z0, zz], [sh.x1, sh.z1, zz], [sh.x0, sh.z1, zz]]
                out.append({"id": sh.id, "role": "TANK_DECK", "item": sh.item, "group": "tank", "parent": t["id"],
                            "level": t["level"], "cut_length": 0.0, "profile": prof, "extrude": [0.0, 0.0, 18.3],
                            "sig": _sig(prof, [0.0, 0.0, 18.3], sh.item)})
    return out
