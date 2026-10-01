"""Formas especiais (Anexo A7): paredes curvas em facetas e pilares isolados."""
from __future__ import annotations

import math

from .. import geometry as g
from ..model import ColumnSpec, CurvedWall, Wall
from .context import Ctx


def facet_walls(cw: CurvedWall, ctx: Ctx) -> list[Wall]:
    C = ctx.rules.data["curved_wall"]
    if cw.radius < C["min_radius"]:
        ctx.issue("V-042", "error", cw.id, f"raio {cw.radius:.0f} mm abaixo do mínimo {C['min_radius']} mm")
    segs = g.facet_arc(cw.center, cw.radius, cw.angle_start, cw.angle_end, C["max_chord"], C["max_sagitta"])
    walls = []
    for i, (a, b) in enumerate(segs, start=1):
        chord = g.dist(a, b)
        sag = g.sagitta(cw.radius, chord)
        dth = g.facet_angle_deg(cw.radius, chord)
        if sag > C["max_sagitta"] + 1e-6:
            ctx.issue("V-043", "error", cw.id, f"flecha {sag:.1f} mm acima do limite")
        if chord < C["min_chord"]:
            ctx.issue("V-048", "warning", cw.id, f"faceta de {chord:.0f} mm abaixo do mínimo")
        walls.append(Wall(id=f"{cw.id}F{i:02d}", level=cw.level, start=a, end=b, height=cw.height,
                          exterior=cw.exterior, bearing=cw.bearing, wall_type=cw.wall_type, facet_of=cw.id))
    ctx.issue("V-000", "info", cw.id, f"parede curva R={cw.radius:.0f} dividida em {len(segs)} facetas de "
                                     f"{g.dist(*segs[0]):.0f} mm (flecha {g.sagitta(cw.radius, g.dist(*segs[0])):.1f} mm)")
    return walls


def frame_column(cs: ColumnSpec, ctx: Ctx) -> None:
    load = cs.tributary_area_m2 * (cs.load_kPa if cs.load_kPa is not None else ctx.rules.data["columns"]["load_factor_kPa"])
    cands = [it for it in ctx.cat.items.values() if it["category"] == "column" and it["system"] == ctx.system
             and it.get("capacity_kN", 0) >= load]
    cid = f"{ctx.pfx}-{cs.level}-{cs.id}"
    if not cands:
        ctx.issue("V-046", "error", cid, f"carga de {load:.1f} kN acima da capacidade dos pilares do catálogo")
        return
    it = min(cands, key=lambda i: i["capacity_kN"])
    m = ctx.new_member("COLUMN", it["id"], cs.level, "column", cid, frame="plan", x0=cs.position[0],
                       x1=cs.position[0], z0=cs.position[1], z1=cs.position[1], orientation="V",
                       cut_length=cs.height, rule="columns",
                       note=f"carga {load:.1f} kN; capacidade de referência {it['capacity_kN']} kN")
    m.id = f"{cid}-COLUMN-01"
    ctx.members.append(m)
    ctx.hw("CHAPA-BASE-PILAR", 1, f"{cid} base")
    ctx.hw("SUPORTE-VIGA-SV1", 1, f"{cid} topo")
    ctx.bearing_points.append(("column", cid, cs.position, cs.level))
