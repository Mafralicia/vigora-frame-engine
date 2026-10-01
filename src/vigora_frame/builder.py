"""Execução completa: projeto -> peças, ligações, placas, ferragens, validações."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from .config import ROOT, Catalog, ConfigError, Rules
from .engine.context import Ctx
from .engine.floors import frame_floor
from .engine.junctions import analyze
from .engine.roofs import check_roof_alignment, frame_roof
from .engine.stairs import frame_stair
from .engine.tanks import plan_tanks
from .engine.special import facet_walls, frame_column
from .engine.walls import frame_wall, prepare
from .model import Project, Result
from .validate import validate


def split_tall_walls(walls, lv, ctx):
    """Parede mais alta que a mesa de fabricação: painel principal até o pé-direito + painel de complemento acima."""
    from .model import Level
    max_h = ctx.rules.limits["panel_table"]["max_height"]
    out, extra = [], {}
    for w in walls:
        if w.height <= max_h + 0.5:
            out.append(w)
            continue
        base = lv[w.level]
        h_low = min(base.height, max_h)
        if any(o.sill + o.height > h_low - 150 for o in w.openings):
            ctx.issue("V-089", "error", w.id, "abertura na altura da divisão do painel de complemento")
        uid = f"{w.level}C{int(round(h_low))}"
        if uid not in extra:
            extra[uid] = Level(id=uid, name=f"{base.name} — complemento", elevation=base.elevation + h_low,
                               height=w.height - h_low)
        lower = w.model_copy(update={"height": h_low})
        upper = w.model_copy(update={"id": w.id + "C", "level": uid, "height": w.height - h_low, "openings": [],
                                     "bearing": False})
        ctx.wall_upper[w.id] = w.height - h_low
        out += [lower, upper]
        ctx.issue("V-000", "info", w.id, f"parede de {w.height:.0f} mm dividida: painel de {h_low:.0f} + "
                                         f"complemento de {w.height - h_low:.0f} mm (mesa até {max_h:.0f} mm)")
    return out, list(extra.values())


def split_crossings(walls, ctx):
    """Cruzamento em X: a parede de menor prioridade é dividida no ponto de cruzamento (vira dois T)."""
    from . import geometry as g
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(walls):
            for b in walls[i + 1:]:
                if a.level != b.level:
                    continue
                p = g.seg_intersection(a.start, a.end, b.start, b.end)
                if p is None:
                    continue
                ta, pa = g.project_param(p, a.start, a.end)
                tb, pb = g.project_param(p, b.start, b.end)
                La, Lb = g.dist(a.start, a.end), g.dist(b.start, b.end)
                if not (5 < ta < La - 5 and 5 < tb < Lb - 5 and pa < 1 and pb < 1):
                    continue
                key = lambda w, L: (w.exterior, w.bearing, L, w.id)
                cut, t_cut, Lc = (b, tb, Lb) if key(a, La) > key(b, Lb) else (a, ta, La)
                pt = (round(p[0], 3), round(p[1], 3))
                ops1 = [o for o in cut.openings if o.offset + o.width < t_cut - 1]
                ops2 = [o.model_copy(update={"offset": o.offset - t_cut}) for o in cut.openings if o.offset > t_cut + 1]
                if len(ops1) + len(ops2) != len(cut.openings):
                    ctx.issue("V-079", "error", cut.id, "abertura sobre o cruzamento de paredes")
                w1 = cut.model_copy(update={"id": cut.id + "A", "end": pt, "openings": ops1})
                w2 = cut.model_copy(update={"id": cut.id + "B", "start": pt, "openings": ops2})
                k = walls.index(cut)
                walls = walls[:k] + [w1, w2] + walls[k + 1:]
                ctx.issue("V-000", "info", cut.id, f"cruzamento em X com {(a if cut is b else b).id}: dividida em {w1.id} e {w2.id}")
                changed = True
                break
            if changed:
                break
    return walls


def load_project(path: str | Path) -> Project:
    return Project.model_validate_json(Path(path).read_text(encoding="utf-8"))


def run(project: Project, root: Path = ROOT) -> Result:
    rules = Rules.load(project.ruleset, root)
    cat = Catalog.load(root)
    if rules.system != project.system:
        raise ConfigError(f"ruleset {rules.name} é {rules.system}, projeto é {project.system}")
    ctx = Ctx(project=project, rules=rules, cat=cat)
    levels = sorted(project.levels, key=lambda l: l.elevation)
    lv = {l.id: l for l in levels}

    walls = list(project.walls)
    for cw in project.curved_walls:
        walls += facet_walls(cw, ctx)
    walls = split_crossings(walls, ctx)
    walls, extra_levels = split_tall_walls(walls, lv, ctx)
    for el in extra_levels:
        lv[el.id] = el
    all_levels = sorted(list(levels) + extra_levels, key=lambda l: l.elevation)
    wall_levels = [l.id for l in levels if any(w.level == l.id for w in walls)]
    top = wall_levels[-1] if wall_levels else None

    depth_of = {}
    for w in walls:
        wt = rules.data["wall_types"][rules.wall_type(w)]
        depth_of[w.id] = w.thickness or cat.depth(wt["stud"])
    junc, problems = analyze(walls, depth_of)
    for code, el, msg in problems:
        ctx.issue(code, "warning" if code == "V-067" else "error", el, msg)

    for w in walls:
        wf = prepare(w, junc[w.id], ctx, top_level=(w.level == top), elevation=lv[w.level].elevation)
        ctx.wall_frames[w.id] = wf
    for w in walls:
        frame_wall(ctx.wall_frames[w.id], ctx)

    for fs in project.floors:
        idx = [l.id for l in levels].index(fs.level)
        below = levels[idx - 1].id if idx > 0 else None
        wb = [wf for wf in ctx.wall_frames.values() if wf.wall.level == below]
        frame_floor(fs, ctx, wb, lv[fs.level].elevation)
    plan_tanks(ctx, levels)          # a caixa vem antes do telhado: o telhado lê o envelope e se adapta
    # telhados de rincão (asas) depois do principal: precisam da superfície do telhado de baixo
    for rs in sorted(project.roofs, key=lambda r: "valley" in r.ends):
        frame_roof(rs, ctx, [wf for wf in ctx.wall_frames.values() if wf.wall.level == rs.level])
    check_roof_alignment(ctx)
    for cs in project.columns:
        frame_column(cs, ctx)
    for st in project.stairs:
        frame_stair(st, ctx, levels, project.floors)

    validate(ctx)

    raw = project.model_dump_json()
    ih = hashlib.sha256(raw.encode()).hexdigest()[:16]
    sev = Counter(i.severity for i in ctx.issues)
    roles = Counter(m.role for m in ctx.members)
    stats = {
        "panels": len(ctx.panels),
        "members": len(ctx.members),
        "members_by_group": dict(Counter(m.group for m in ctx.members)),
        "members_by_role": dict(sorted(roles.items())),
        "connections": len(ctx.connections),
        "sheets": len(ctx.sheets),
        "trusses": sum(t.count for t in ctx.trusses),
        "issues": dict(sev),
        "weight_kg_members": round(sum(m.weight_kg for m in ctx.members), 1),
        "special_members": sum(1 for m in ctx.members if m.special),
        "unique_panels": len({p.signature for p in ctx.panels}),
        "placements": ctx.placements,
        "stairs": ctx.stairs,
        "tanks": ctx.tanks,
        "roofs": [dict(v, id=k, ends=list(next((r.ends for r in project.roofs if k.endswith("-" + r.id)), ("gable", "gable"))))
                  for k, v in ctx.roof_info.items()],
        "floor_holes": [[list(map(list, h)) for h in f.holes] for f in project.floors],
        "levels": {l.id: {"elevation": l.elevation, "name": l.name} for l in all_levels},
    }
    res = Result(project=project.id, project_name=project.name, system=project.system, ruleset=rules.name,
                 ruleset_approved=rules.approved(), run_id=f"{ih[:8]}-{rules.digest[:6]}", input_hash=ih,
                 panels=ctx.panels, members=ctx.members, connections=ctx.connections, sheets=ctx.sheets,
                 hardware=ctx.hardware, trusses=ctx.trusses, issues=ctx.issues, stats=stats, meta=project.meta)
    if ctx.tanks:                     # colisão 3D da caixa com o modelo final (depois de tudo gerado)
        from .engine.tanks import check_tank_clashes
        extra = check_tank_clashes(res)
        res.issues += extra
        for i in extra:
            res.stats["issues"][i.severity] = res.stats["issues"].get(i.severity, 0) + 1
    return res


def save_result(res: Result, path: str | Path) -> None:
    Path(path).write_text(res.model_dump_json(indent=1), encoding="utf-8")


def load_result(path: str | Path) -> Result:
    return Result.model_validate_json(Path(path).read_text(encoding="utf-8"))
