"""Motor de paredes (seções 7, 8 e Anexos A3, A4, A5, A10).

Referencial de framing de cada parede: x = 0 no início do comprimento de framing,
ao longo do eixo; z = 0 na base da placa inferior. Os painéis usam o mesmo
referencial deslocado pelo início do painel.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

from .. import geometry as g
from ..model import Connection, Member, Opening, Panel, Sheet, Wall
from .context import Ctx, qty_for
from .junctions import WallJunctions

VERTICAL = {"STUD", "STUD_END", "KING", "JACK", "CRIPPLE", "BACKER", "SHEET_STUD", "NAILER"}
FULL_HEIGHT = {"STUD", "STUD_END", "KING", "BACKER", "SHEET_STUD"}
ROLE_ORDER = ["BOTTOM_PLATE", "TOP_PLATE", "STUD_END", "STUD", "SHEET_STUD", "BACKER", "KING", "JACK",
              "HEADER", "PACKER", "SILL", "CRIPPLE", "NAILER", "BLOCK", "STRAP", "BRACE_STRAP", "ARCH_FILLER"]
EPS = 0.01
TOUCH = 2.5      # folga máxima para considerar contato (mm)
CLASH = 0.5      # sobreposição mínima para considerar interferência (mm)
MIN_BLOCK = 60   # bloqueio menor que isso não é fabricado (a junta apoia nas peças vizinhas)
MIN_CLEAR = 60   # vão livre mínimo entre peças paralelas; abaixo disso as peças se encostam (sem vão aleatório)
MOVABLE = {"STUD", "SHEET_STUD"}


# ------------------------------------------------------------------ estruturas
@dataclass
class OpeningFrame:
    op: Opening
    xl: float
    xr: float
    zb: float
    zt: float
    door: bool
    load_case: str
    header_item: str | None
    header_plies: int
    j: int
    k: int
    kings_left: int = 0
    kings_right: int = 0

    @property
    def span(self):
        return self.xr - self.xl

    @property
    def zone_l(self):
        return self.xl - (self.j + self.kings_left) * self._t

    @property
    def zone_r(self):
        return self.xr + (self.j + self.kings_right) * self._t

    _t: float = 38.0


@dataclass
class WallFrame:
    wall: Wall
    wtype: str
    wt: dict
    stud: str
    plate: str
    t: float
    depth: float
    spacing: float
    H: float
    pt: float
    n_top: int
    clr: float
    L: float
    ext_start: float
    ext_end: float
    dirv: tuple
    origin: tuple
    junc: WallJunctions
    elevation: float
    top_level: bool
    braced: bool
    openings: list[OpeningFrame] = field(default_factory=list)
    tees: list[tuple[float, float, str]] = field(default_factory=list)
    panels: list[tuple[float, float]] = field(default_factory=list)
    stud_centers: list[float] = field(default_factory=list)   # framing x, verticais de altura total
    panel_ids: list[str] = field(default_factory=list)
    grid0: float = 0.0            # primeira linha da grade global no referencial de framing

    def grid_from(self, step: float) -> float:
        u0 = self.origin[0] * self.dirv[0] + self.origin[1] * self.dirv[1]
        return (-u0) % step

    @property
    def z_stud0(self):
        return self.pt + self.clr / 2

    @property
    def z_stud1(self):
        return self.H - self.n_top * self.pt - self.clr / 2

    @property
    def panel_height(self):
        """Altura do painel de fábrica (sem a placa de capa, montada em obra)."""
        return self.H - (self.n_top - 1) * self.pt if self.n_top > 1 else self.H

    def to_global(self, x: float) -> tuple[float, float]:
        return (self.origin[0] + self.dirv[0] * x, self.origin[1] + self.dirv[1] * x)

    @property
    def axis(self) -> str:
        return "x" if abs(self.dirv[0]) >= abs(self.dirv[1]) else "y"


@dataclass
class R:
    """Retângulo de trabalho (coordenadas de framing da parede)."""
    role: str
    x0: float
    x1: float
    z0: float
    z1: float
    item: str
    orient: str = "V"
    plies: int = 1
    opening: str | None = None
    rule: str = ""
    note: str = ""
    plane: str = "core"
    special: bool = False
    polygon: list | None = None
    cut: float = 0.0
    shifted: bool = False
    fixed: bool = False      # aço: montante da grade que recebe treliça/viga (não se move)

    @property
    def c(self):
        return (self.x0 + self.x1) / 2


# ------------------------------------------------------------------ preparação
def prepare(wall: Wall, junc: WallJunctions, ctx: Ctx, top_level: bool, elevation: float) -> WallFrame:
    Rd = ctx.rules.data
    cat = ctx.cat
    wtype = ctx.rules.wall_type(wall)
    wt = Rd["wall_types"][wtype]
    stud = wt["stud"]
    plate = wt.get("track", stud)
    t = cat.face(stud)
    depth = cat.depth(stud)
    pt = cat.face(plate) if ctx.system == "wood" else cat.thickness(plate)
    n_top = Rd["plates"]["top"]
    axis_len = g.dist(wall.start, wall.end)
    dirv = g.unit(g.sub(wall.end, wall.start))
    es, ee = junc.start.ext, junc.end.ext
    L = axis_len + es + ee
    origin = g.sub(wall.start, g.mul(dirv, es))
    braced = wall.braced if wall.braced is not None else wall.exterior
    wf = WallFrame(wall=wall, wtype=wtype, wt=wt, stud=stud, plate=plate, t=t, depth=depth,
                   spacing=float(wt["spacing"]), H=wall.height, pt=pt, n_top=n_top,
                   clr=float(Rd.get("stud_clearance", 0)), L=L, ext_start=es, ext_end=ee,
                   dirv=dirv, origin=origin, junc=junc, elevation=elevation, top_level=top_level,
                   braced=braced)
    wf.grid0 = wf.grid_from(wf.spacing)
    tees = []
    for tp, tw_, oid in sorted((tp + es, w_, oid) for tp, w_, oid in junc.tees):
        if tees and abs(tees[-1][0] - tp) < 1.0:          # cruzamento em X: um bloco atende os dois lados
            tees[-1] = (tees[-1][0], max(tees[-1][1], tw_), tees[-1][2] + "+" + oid)
        else:
            tees.append((tp, tw_, oid))
    wf.tees = tees
    _prepare_openings(wf, ctx)
    wf.panels = panelize_wall(wf, ctx)
    return wf


def _prepare_openings(wf: WallFrame, ctx: Ctx):
    o = ctx.rules.data["openings"]
    cps, ct = o["clearance_per_side"], o["clearance_top"]
    w = wf.wall
    for op in sorted(w.openings, key=lambda q: q.offset):
        x = op.offset + wf.ext_start
        xl, xr = x - cps, x + op.width + cps
        door = op.kind in ("door", "passage") and op.sill <= 0
        zb = 0.0 if door else op.sill - cps
        zt = op.sill + op.height + ct
        if not w.bearing:
            lc = "nao_portante"
        elif wf.top_level:
            lc = "cobertura"
        else:
            lc = "piso_e_cobertura"
        row = ctx.rules.header_for(lc, xr - xl)
        if row is None:
            ctx.issue("V-001", "error", f"{w.id}/{op.id}",
                      f"vão estrutural de {xr - xl:.0f} mm fora da tabela de verga ({lc}); verga não gerada")
            of = OpeningFrame(op, xl, xr, zb, zt, door, lc, None, 0, 1, 1)
        else:
            of = OpeningFrame(op, xl, xr, zb, zt, door, lc, row.item, row.plies, row.jack_per_side,
                              row.king_per_side)
        of._t = wf.t
        of.kings_left = of.kings_right = of.k
        wf.openings.append(of)
    # aberturas vizinhas: montante compartilhado ou sobreposição
    for a, b in zip(wf.openings, wf.openings[1:]):
        jr = a.xr + a.j * wf.t
        jl = b.xl - b.j * wf.t
        if jl < jr - EPS:
            ctx.issue("V-022", "error", f"{wf.wall.id}/{a.op.id}+{b.op.id}",
                      "aberturas sobrepostas (as ombreiras se cruzam)")
        elif jl - jr < (a.k + b.k) * wf.t - EPS:
            ctx.issue("V-019", "warning", f"{wf.wall.id}/{a.op.id}+{b.op.id}",
                      f"aberturas a {jl - jr:.0f} mm: ombreira compartilhada entre os vãos")
            n = int((jl - jr + EPS) // wf.t)
            a.kings_right = n
            b.kings_left = 0
    # aço: montante da grade a menos de MIN_CLEAR do king -> ombreira encosta nele (folga do caixilho cresce)
    if ctx.system == "steel":
        s_ = wf.spacing
        for of in wf.openings:
            t = wf.t
            for side in (-1, 1):
                face = of.zone_l if side < 0 else of.zone_r
                k0 = math.floor((face - wf.grid0) / s_) - 1
                for k in range(k0, k0 + 4):
                    c = wf.grid0 + k * s_
                    gap = (face - (c + t / 2)) if side < 0 else ((c - t / 2) - face)
                    if CLASH < gap < MIN_CLEAR:
                        if side < 0:
                            of.xl -= gap
                        else:
                            of.xr += gap
                        ctx.issue("V-000", "info", f"{wf.wall.id}/{of.op.id}",
                                  f"ombreira deslocada {gap:.0f} mm para encostar no montante alinhado; "
                                  f"folga do caixilho desse lado = {ctx.rules.data['openings']['clearance_per_side'] + gap:.0f} mm")

    # distâncias a cantos e encontros
    md = ctx.rules.data["openings"]["min_distance_to_corner"]
    for of in wf.openings:
        lo = wf.t + (wf.junc.start.other_depth + wf.t if wf.junc.start.kind == "through" else 0)
        hi = wf.L - wf.t - (wf.junc.end.other_depth + wf.t if wf.junc.end.kind == "through" else 0)
        if of.zone_l < lo - EPS or of.zone_r > hi + EPS:
            ctx.issue("V-018", "error", f"{wf.wall.id}/{of.op.id}",
                      "abertura invade a zona de canto (ombreiras sem espaço)")
        elif of.zone_l < lo + md or of.zone_r > hi - md:
            ctx.issue("V-018", "warning", f"{wf.wall.id}/{of.op.id}",
                      f"abertura a menos de {md} mm do reforço de canto")
        for tp, tw, oid in wf.tees:
            if of.zone_l - wf.t < tp + tw / 2 and tp - tw / 2 < of.zone_r + wf.t:
                ctx.issue("V-069", "error", f"{wf.wall.id}/{of.op.id}",
                          f"parede {oid} encontra esta parede sobre a abertura")
        hd = ctx.cat.depth(of.header_item) if of.header_item else 0
        if of.zt + hd > wf.z_stud1 + EPS:
            ctx.issue("V-016", "error", f"{wf.wall.id}/{of.op.id}",
                      f"verga ({hd:.0f} mm) não cabe entre o topo do vão e a placa superior")
        if not of.door and of.zb - wf.pt < wf.z_stud0 + 1:
            ctx.issue("V-070", "error", f"{wf.wall.id}/{of.op.id}", "peitoril baixo demais para o peitoril estrutural")


def panelize_wall(wf: WallFrame, ctx: Ctx) -> list[tuple[float, float]]:
    P = ctx.rules.data["panels"]
    max_len = min(P["max_length"], max(ctx.cat.stock_lengths(wf.plate)))
    mj0 = P["min_joint_to_opening"]
    # tenta a folga padrão; se não houver junta possível (aberturas em sequência), reduz até 1 peça
    for mj in (mj0, wf.t + MIN_CLEAR, wf.t):
        forb = [(of.zone_l - mj, of.zone_r + mj) for of in wf.openings]
        forb += [(tp - tw / 2 - 3 * wf.t, tp + tw / 2 + 3 * wf.t) for tp, tw, _ in wf.tees]
        if ctx.system == "wood" and wf.n_top > 1:
            lap = ctx.rules.data["plates"]["cap_lap_min"]
            forb += [(tp - tw / 2 - lap, tp + tw / 2 + lap) for tp, tw, _ in wf.tees]
        panels, ok = panelize(wf.L, forb, max_len, P["min_length"], wf.spacing, wf.grid0)
        if ok and mj < wf.t + MIN_CLEAR - EPS:
            # junta perto da ombreira: encosta o montante de borda no king (sem vão entre eles)
            js = [b for a, b in panels[:-1]]
            for i, j in enumerate(js):
                for of in wf.openings:
                    if of.zone_l - wf.t - MIN_CLEAR < j < of.zone_l - wf.t:
                        js[i] = of.zone_l - wf.t
                    elif of.zone_r + wf.t < j < of.zone_r + wf.t + MIN_CLEAR:
                        js[i] = of.zone_r + wf.t
            cuts = [0.0] + js + [wf.L]
            new = list(zip(cuts, cuts[1:]))
            if all(b - a <= max_len + EPS for a, b in new):
                panels = new
            else:
                ok = False
        if ok:
            if mj < mj0:
                ctx.issue("V-073", "warning", wf.wall.id,
                          f"aberturas em sequência: junta de painel a {mj:.0f} mm da ombreira (padrão {mj0})")
            return panels
    ctx.issue("V-002", "error", wf.wall.id,
              "não foi possível dividir a parede em painéis dentro dos limites; ver aberturas e encontros")
    return panels


def panelize(L: float, forbidden: list[tuple[float, float]], max_len: float, min_len: float,
             grid: float, grid0: float = 0.0) -> tuple[list[tuple[float, float]], bool]:
    """Divide [0, L] em painéis. Juntas fora das zonas proibidas, preferindo a grade."""
    if L <= max_len:
        return [(0.0, L)], True

    def allowed(x):
        return all(not (a < x < b) for a, b in forbidden)

    n0 = math.ceil(L / max_len - 1e-9)
    for n in range(n0, n0 + 8):
        joints, start, ok = [], 0.0, True
        for i in range(1, n):
            rem = n - i
            target = start + (L - start) / (rem + 1)
            lo = max(start + min_len, L - rem * max_len)
            hi = min(start + max_len, L - rem * min_len)
            if lo > hi + EPS:
                ok = False
                break
            cands = [grid0 + k * grid for k in range(int((lo - grid0) // grid), int((hi - grid0) // grid) + 2)
                     if lo - EPS <= grid0 + k * grid <= hi + EPS and allowed(grid0 + k * grid)]
            if not cands:
                pts = [lo, hi] + [p for ab in forbidden for p in ab if lo <= p <= hi]
                cands = [p for p in pts if allowed(p)]
            if not cands:
                ok = False
                break
            x = min(cands, key=lambda c: (abs(c - target), c))
            joints.append(x)
            start = x
        if ok and L - start <= max_len + EPS:
            edges = [0.0] + joints + [L]
            return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)], True
    step = L / n0
    return [(i * step, (i + 1) * step) for i in range(n0)], False


# ------------------------------------------------------------------ geração
def frame_wall(wf: WallFrame, ctx: Ctx) -> None:
    w = wf.wall
    for pi, (xs, xe) in enumerate(wf.panels, start=1):
        _frame_panel(wf, ctx, pi, xs, xe)
    if ctx.system == "wood" and wf.n_top > 1:
        _cap_plates(wf, ctx)
    _bracing_segments(wf, ctx)
    # conexões entre painéis vizinhos (LG-06)
    conn = ctx.rules.connection("LG-06")
    ends = {}
    for m in ctx.members:
        if m.group == "wall" and m.frame == "panel" and m.role == "STUD_END" and m.parent in wf.panel_ids:
            ends.setdefault(m.parent, []).append(m)
    for a, b in zip(wf.panel_ids, wf.panel_ids[1:]):
        ea = max(ends.get(a, []), key=lambda m: m.x0, default=None)
        eb = min(ends.get(b, []), key=lambda m: m.x0, default=None)
        if ea and eb:
            ctx.connections.append(_conn(ctx, ea.id, eb.id, "LG-06", conn, ea.cut_length))


def _frame_panel(wf: WallFrame, ctx: Ctx, pi: int, xs: float, xe: float):
    w = wf.wall
    t, s, H = wf.t, wf.spacing, wf.H
    stud, plate = wf.stud, wf.plate
    z0s, z1s = wf.z_stud0, wf.z_stud1
    rects: list[R] = []
    tol = float(ctx.rules.data.get("spacing_tolerance", 0))
    ops = [of for of in wf.openings if of.zone_l < xe and of.zone_r > xs]
    for of in ops:
        if of.zone_l < xs - EPS or of.zone_r > xe + EPS:
            ctx.issue("V-022", "error", f"{w.id}/{of.op.id}", "abertura cruza a junta entre painéis")

    # 1. placas / guias
    cuts = sorted((of.xl, of.xr) for of in ops if of.door)
    x = xs
    for a, b in cuts:
        if a > x + EPS:
            rects.append(R("BOTTOM_PLATE", x, a, 0, wf.pt, plate, "H", rule="plates.bottom"))
        x = max(x, b)
    if xe > x + EPS:
        rects.append(R("BOTTOM_PLATE", x, xe, 0, wf.pt, plate, "H", rule="plates.bottom"))
    ztp0 = H - wf.n_top * wf.pt
    rects.append(R("TOP_PLATE", xs, xe, ztp0, ztp0 + wf.pt, plate, "H", rule="plates.top"))

    # 2. verticais fixas de altura total
    def end_piece(info):
        """Ponta em meia-esquadria: montante chanfrado; se o chanfro consumir o montante, pilarete."""
        if info.kind != "miter":
            return stud, t, ""
        if t - info.bevel >= 10:
            return stud, t, f"chanfro de {info.miter_deg:.1f}° na espessura (sobra {t - info.bevel:.0f} mm na face interna)"
        posts = sorted([it for it in ctx.cat.items.values() if it["category"] == "column" and it["system"] == ctx.system
                        and ctx.cat.face(it["id"]) - info.bevel >= 10], key=lambda it: ctx.cat.face(it["id"]))
        if not posts:
            ctx.issue("V-078", "error", w.id, f"canto de {info.miter_deg:.0f}° sem peça de ponta no catálogo")
            return stud, t, ""
        it = posts[0]["id"]
        return it, ctx.cat.face(it), f"pilarete chanfrado a {info.miter_deg:.1f}° (CNC)"

    si, sw, sn = end_piece(wf.junc.start) if xs < EPS else (stud, t, "")
    ei, ew, en = end_piece(wf.junc.end) if xe > wf.L - EPS else (stud, t, "")
    fh: list[R] = [R("STUD_END", xs, xs + sw, z0s, z1s, si, rule="panel.end", note=sn, special=bool(sn and si != stud)),
                   R("STUD_END", xe - ew, xe, z0s, z1s, ei, rule="panel.end", note=en, special=bool(en and ei != stud))]
    for end, x_at, sign in (("start", 0.0, 1), ("end", wf.L, -1)):
        info = getattr(wf.junc, end)
        if info.kind == "through" and xs - EPS <= x_at <= xe + EPS:
            od = info.other_depth
            if od - t >= MIN_CLEAR:          # um reforço, com vão livre suficiente para isolamento
                pos = [x_at + sign * (od + t / 2)]
            else:                            # reforços encostados até cobrir a face interna + 25 mm
                n = math.ceil((od + 25) / t - 1e-9)
                pos = [x_at + sign * (t * k + t / 2) for k in range(1, n)]
            for p_ in pos:
                fh.append(R("BACKER", p_ - t / 2, p_ + t / 2, z0s, z1s, stud, rule="corners.corner_style",
                            note=f"reforço de canto para {info.other}"))
    for tp, tw, oid in wf.tees:
        if xs < tp < xe:
            n = math.ceil((tw + 50) / t - 1e-9)        # bloco contínuo: 25 mm de apoio de cada lado
            x0b = tp - n * t / 2
            for k in range(n):
                fh.append(R("BACKER", x0b + k * t, x0b + (k + 1) * t, z0s, z1s, stud,
                            rule="corners.t_junction_style", note=f"encontro em T com {oid} (bloco de {n} peças)"))
    for of in ops:
        oid = of.op.id
        for i in range(of.j):
            rects.append(R("JACK", of.xl - (i + 1) * t, of.xl - i * t, z0s, of.zt, stud, opening=oid,
                           rule="openings.jack"))
            rects.append(R("JACK", of.xr + i * t, of.xr + (i + 1) * t, z0s, of.zt, stud, opening=oid,
                           rule="openings.jack"))
        for i in range(of.kings_left):
            x1 = of.xl - of.j * t - i * t
            fh.append(R("KING", x1 - t, x1, z0s, z1s, stud, opening=oid, rule="openings.king"))
        for i in range(of.kings_right):
            x0 = of.xr + of.j * t + i * t
            fh.append(R("KING", x0, x0 + t, z0s, z1s, stud, opening=oid, rule="openings.king"))
    # montante compartilhado já contado pela abertura da esquerda
    zones = [(of.zone_l, of.zone_r) for of in ops]

    def clashes(a0, a1, lst):
        return [r for r in lst if a0 < r.x1 - CLASH and a1 > r.x0 + CLASH]

    def in_zone(a0, a1):
        return any(a0 < zr - CLASH and a1 > zl + CLASH for zl, zr in zones)

    # 3. montantes na grade (referência global da parede)
    g0 = wf.grid0
    kmin, kmax = int((xs - g0) // s) - 1, int((xe - g0) // s) + 1
    cripple_pos: dict[str, list[float]] = {of.op.id: [] for of in ops}
    top_extra: dict[str, list[float]] = {of.op.id: [] for of in ops}
    for k in range(kmin, kmax + 1):
        c = g0 + k * s
        a0, a1 = c - t / 2, c + t / 2
        if a0 < xs - EPS or a1 > xe + EPS:
            if not (xs - EPS <= c <= xe + EPS):
                continue
        hit_ro = [of for of in ops if of.xl < c < of.xr]
        if hit_ro:
            cripple_pos[hit_ro[0].op.id].append(c)
            continue
        if in_zone(a0, a1):
            continue
        cl = clashes(a0, a1, fh)
        if not cl:
            if a0 >= xs - EPS and a1 <= xe + EPS:
                fh.append(R("STUD", a0, a1, z0s, z1s, stud, rule="studs.grid", fixed=ctx.system == "steel"))
            continue
        obs = cl[0]
        n0, n1 = (obs.x0 - t, obs.x0) if c < obs.c else (obs.x1, obs.x1 + t)
        if n0 < xs - EPS or n1 > xe + EPS or clashes(n0, n1, fh) or in_zone(n0, n1):
            continue
        fh.append(R("STUD", n0, n1, z0s, z1s, stud, rule="studs.grid", shifted=True,
                    note="deslocado da grade para não interferir"))

    # 4. remove deslocados redundantes e completa vãos acima do máximo
    def barrier_between(a: R, b: R):
        return any(a.c <= of.xl + EPS and of.xr <= b.c + EPS for of in ops)

    changed = True
    while changed:
        changed = False
        fh.sort(key=lambda r: r.c)
        for i in range(1, len(fh) - 1):
            r = fh[i]
            if r.shifted and not barrier_between(fh[i - 1], fh[i + 1]) and fh[i + 1].c - fh[i - 1].c <= s + tol + EPS:
                fh.pop(i)
                changed = True
                break
    fh.sort(key=lambda r: r.c)
    extra = []
    for a, b in zip(fh, fh[1:]):
        if barrier_between(a, b):
            continue
        d = b.c - a.c
        if d > s + tol + EPS:
            n = math.ceil(d / (s + tol) - 1e-9) - 1
            for i in range(1, n + 1):
                c = a.c + d * i / (n + 1)
                extra.append(R("STUD", c - t / 2, c + t / 2, z0s, z1s, stud, rule="studs.max_spacing",
                               note="inserido para respeitar o espaçamento máximo"))
    fh += extra

    # 5. montantes nas juntas verticais das placas estruturais
    sheet_item = wf.wt.get("sheathing")
    sheet_W = sheet_H = 0.0
    if sheet_item:
        sheet_W, sheet_H = ctx.cat.get(sheet_item)["size"]
        pass    # juntas das placas escolhidas depois, sobre montantes existentes (etapa 6b)
    _tidy_line(fh, s + tol, t, lambda a, b: barrier_between(a, b))
    rects += fh

    # 6. aberturas: verga, peitoril, cripples, enchimento de arco
    min_cr = ctx.rules.data["openings"]["min_cripple_length"]
    joints_h = [float(sheet_H)] if sheet_item and wf.panel_height > sheet_H + EPS else []
    for of in ops:
        oid = of.op.id
        hx0, hx1 = of.xl - of.j * t, of.xr + of.j * t
        top_under = z1s
        if of.header_item:
            hd = ctx.cat.depth(of.header_item)
            hitem = of.header_item
            # verga cujo topo pararia logo abaixo de uma junta horizontal de placa: sobe até apoiar a junta
            for j in joints_h:
                top = of.zt + hd
                if j - 9 - t / 2 - MIN_CLEAR < top < j + 9:
                    need = j + 9 - of.zt
                    cands = [it for it in ctx.cat.items.values()
                             if it["system"] == ctx.system and it["category"] in ("lumber", "engineered", "stud", "joist")
                             and ctx.cat.face(it["id"]) == ctx.cat.face(hitem)
                             and need <= ctx.cat.depth(it["id"]) <= top_under - of.zt]
                    if cands:
                        best = min(cands, key=lambda it: ctx.cat.depth(it["id"]))
                        hitem, hd = best["id"], ctx.cat.depth(best["id"])
            of.header_item = hitem
            hz1 = min(of.zt + hd, top_under)
            rects.append(R("HEADER", hx0, hx1, of.zt, hz1, of.header_item, "H", plies=of.header_plies,
                           opening=oid, rule="openings.header_table",
                           note=f"caso {of.load_case}" + ("; verga aumentada para apoiar a junta da placa"
                                                          if hitem != ctx.rules.header_for(of.load_case, of.span).item else "")))
            gap = top_under - hz1
        else:
            hz1, gap = of.zt, top_under - of.zt
        # posições dos cripples
        pos = sorted(set(round(min(max(c, of.xl + t / 2), of.xr - t / 2), 1) for c in cripple_pos[oid]))
        dedup = []
        for c in pos:
            if not dedup or c - dedup[-1] >= t - EPS:
                dedup.append(c)
        def filled(lo_c, hi_c):
            chain = [lo_c] + dedup + [hi_c]
            fill = []
            for a, b in zip(chain, chain[1:]):
                d = b - a
                if d > s + tol + EPS:
                    n = math.ceil(d / (s + tol) - 1e-9) - 1
                    fill += [a + d * i / (n + 1) for i in range(1, n + 1)]
            return sorted(dedup + fill)

        # acima da verga os vizinhos são os kings; abaixo do peitoril, os jacks
        extra = [min(max(c, hx0 + t / 2), hx1 - t / 2) for c in top_extra[oid]]
        base = dedup
        dedup = sorted(set(dedup) | set(extra))
        dd = []
        for c in dedup:
            if not dd or c - dd[-1] >= t - EPS:
                dd.append(c)
        dedup = dd
        cr_top = _tidy_centers(filled(hx0 - t / 2, hx1 + t / 2), hx0 - t / 2, hx1 + t / 2, s + tol, t,
                               keep=[min(max(c, hx0 + t / 2), hx1 - t / 2) for c in top_extra[oid]])
        dedup = base
        cr = _tidy_centers(filled(of.xl - t / 2, of.xr + t / 2), of.xl - t / 2, of.xr + t / 2, s + tol, t)
        if gap >= min_cr:
            for c in cr_top:
                rects.append(R("CRIPPLE", c - t / 2, c + t / 2, hz1, top_under, stud, opening=oid,
                               rule="openings.cripples"))
        elif gap > 1:
            rects.append(R("PACKER", hx0, hx1, hz1, top_under, stud, "H", opening=oid,
                           rule="openings.packer", note=f"calço de {gap:.0f} mm serrado da peça", special=True))
        if not of.door:
            sz0, sz1 = of.zb - wf.pt, of.zb
            rects.append(R("SILL", of.xl, of.xr, sz0, sz1, plate, "H", opening=oid, rule="openings.sill"))
            below = sz0 - z0s
            if below >= min_cr:
                for c in cr:
                    rects.append(R("CRIPPLE", c - t / 2, c + t / 2, z0s, sz0, stud, opening=oid,
                                   rule="openings.cripples"))
            elif below > 1:
                rects.append(R("PACKER", of.xl, of.xr, z0s, sz0, stud, "H", opening=oid,
                               rule="openings.packer", note=f"calço de {below:.0f} mm", special=True))
        if of.op.kind == "arch" and of.op.rise > 0:
            spring = of.op.sill + of.op.height - of.op.rise
            polys = g.arch_filler_polygons(of.op.width, of.op.rise, spring)
            x_op = of.op.offset + wf.ext_start
            for poly in polys:
                pp = [(x_op + px, pz) for px, pz in poly]
                xs_ = [p[0] for p in pp]
                zs_ = [p[1] for p in pp]
                rects.append(R("ARCH_FILLER", min(xs_), max(xs_), min(zs_), max(zs_), stud, "P",
                               opening=oid, rule="openings.arch", special=True, polygon=pp,
                               note=f"corte CNC, raio {g.arch_radius(of.op.width, of.op.rise):.0f} mm"))

    # 6b. paginação das placas: juntas verticais sobre montantes existentes, junta horizontal livre de vergas
    sheet_cols, sheet_rows = [], []
    if sheet_item:
        sheet_cols, fallback = _sheet_columns(rects, ops, xs, xe, sheet_W, wf.panel_height)
        if fallback:
            _edge_support(rects, fallback, ops, z0s, z1s, stud, t, xs, xe, ctx, w, pi)
        sheet_rows = _sheet_rows(rects, wf.panel_height, sheet_H, t, z1s)

    # 7. bloqueios (travamentos)
    Bk = ctx.rules.data["blocking"]
    zlines = set()
    joint_lines = set()
    for z in Bk.get("fixed_rows", []):                    # linhas padronizadas em todas as paredes
        if z0s + t / 2 <= z <= z1s - t / 2:
            zlines.add(float(z))
    if Bk.get("when_no_structural_sheathing") and not sheet_item and not Bk.get("fixed_rows"):
        z = Bk["spacing_vertical"]
        while z < z1s - t:
            zlines.add(float(z))
            z += Bk["spacing_vertical"]
    if sheet_item and Bk.get("at_sheathing_joints"):
        for z in sheet_rows[1:-1]:
            if z0s + t / 2 <= z <= z1s - t / 2:
                zlines.add(float(z))
                joint_lines.add(float(z))
    horiz = [r for r in rects if r.orient in ("H", "P")]
    item_b = plate if ctx.system == "steel" else stud

    def hclash(x0, x1, z0, z1, margin=0.0):
        return [hr for hr in horiz if hr.x0 < x1 - CLASH and hr.x1 > x0 + CLASH and hr.z0 < z1 - CLASH + margin
                and hr.z1 > z0 + CLASH - margin]

    def fill_band(x_lo, x_hi, bza, bzb, min_gap=MIN_BLOCK):
        """Bloqueios entre as verticais que cobrem a faixa [bza, bzb] dentro de [x_lo, x_hi]."""
        vs = sorted([r for r in rects if r.role in VERTICAL and r.z0 <= bza + EPS and r.z1 >= bzb - EPS
                     and r.x1 > x_lo - EPS and r.x0 < x_hi + EPS], key=lambda r: r.x0)
        for a, b in zip(vs, vs[1:]):
            if b.x0 - a.x1 < min_gap:
                continue
            mid = (a.x1 + b.x0) / 2
            if any(of.xl < mid < of.xr and of.zb < (bza + bzb) / 2 < of.zt for of in ops):
                continue
            if hclash(a.x1, b.x0, bza, bzb):
                continue
            rects.append(R("BLOCK", a.x1, b.x0, bza, bzb, item_b, "H", rule="blocking",
                           note="bloqueador de guia" if ctx.system == "steel" else ""))
            horiz.append(rects[-1])

    for z in sorted(zlines):
        za, zb_ = z - t / 2, z + t / 2
        mg = MIN_BLOCK                      # nem na junta da placa: bloqueio < 60 mm não é fabricado
        vs = sorted([r for r in rects if r.role in VERTICAL and r.z0 <= za + EPS and r.z1 >= zb_ - EPS],
                    key=lambda r: r.x0)
        for a, b in zip(vs, vs[1:]):
            if b.x0 - a.x1 < mg:
                continue
            hit = hclash(a.x1, b.x0, za, zb_, margin=MIN_CLEAR)
            if not hit:
                fill_band(a.x0, b.x1, za, zb_, mg)
                continue
            hr = hit[0]
            joint = z in joint_lines
            if hr.z1 <= z and hr.z1 > za - MIN_CLEAR:           # verga/peitoril logo abaixo: encosta em cima
                if not joint or hr.z1 + t >= z + 9 or hr.z1 >= z - 9:
                    fill_band(a.x0, b.x1, hr.z1, hr.z1 + t, mg)
                else:                                          # junta acima do alcance: camadas encostadas
                    n_l = math.ceil((z + 9 - hr.z1) / t - 1e-9)
                    for k_ in range(n_l):
                        fill_band(a.x0, b.x1, hr.z1 + k_ * t, hr.z1 + (k_ + 1) * t, mg)
            elif hr.z0 >= z and hr.z0 < zb_ + MIN_CLEAR:        # logo acima: encosta embaixo
                if not joint or hr.z0 - t <= z - 9 or hr.z0 <= z + 9:
                    fill_band(a.x0, b.x1, hr.z0 - t, hr.z0, mg)
        if ctx.system == "steel" and Bk.get("strap"):
            rects.append(R("STRAP", xs, xe, z - 20, z + 20, Bk["strap"], "H", plies=2, plane="face",
                           rule="blocking.strap", note="fita de travamento nas duas faces"))

    # 8. contraventamento em X (aço)
    if ctx.system == "steel" and wf.braced and ctx.rules.data["bracing"].get("strap_x"):
        _strap_x(wf, ctx, rects, xs, xe, ops)

    # 9. materializa peças no referencial do painel
    panel_id = f"{ctx.pfx}-{w.level}-{w.id}-PN{pi:02d}"
    wf.panel_ids.append(panel_id)
    ctx.panel_ros[panel_id] = [(of.xl - xs, of.xr - xs, of.zb, of.zt) for of in ops]
    ctx.panel_bands[panel_id] = (z0s, z1s, wf.spacing + tol)
    members = []
    for r in rects:
        poly = [(px - xs, pz) for px, pz in r.polygon] if r.polygon else None
        m = ctx.new_member(r.role, r.item, w.level, "wall", panel_id, frame="panel",
                           x0=round(r.x0 - xs, 2), x1=round(r.x1 - xs, 2), z0=round(r.z0, 2), z1=round(r.z1, 2),
                           orientation=r.orient, plies=r.plies, opening=r.opening, rule=r.rule, note=r.note,
                           plane=r.plane, special=r.special, polygon=poly, cut_length=r.cut)
        if m.role in ("BOTTOM_PLATE", "TOP_PLATE"):
            if xs < EPS and abs(m.x0) < EPS and wf.junc.start.kind == "miter":
                m.angle_a = round(90 - wf.junc.start.miter_deg, 2)
                m.note = "ponta em meia-esquadria (comprimento na ponta longa)"
            if xe > wf.L - EPS and abs(m.x1 - (xe - xs)) < EPS and wf.junc.end.kind == "miter":
                m.angle_b = round(90 - wf.junc.end.miter_deg, 2)
                m.note = "ponta em meia-esquadria (comprimento na ponta longa)"
        members.append(m)
    _assign_ids(members, panel_id)
    ctx.members += members
    for r in fh:
        wf.stud_centers.append(r.c)

    # 10. placas estruturais
    sheets = []
    if sheet_item:
        Hs = wf.panel_height
        n = 0
        Lp = xe - xs
        cols = [c - xs for c in sheet_cols]
        for x, xn in zip(cols, cols[1:]):
            wcol = xn - x
            for z, zn in zip(sheet_rows, sheet_rows[1:]):
                hrow = zn - z
                cut = []
                full_void = False
                for of in ops:
                    cx0, cx1 = max(x, of.xl - xs), min(x + wcol, of.xr - xs)
                    cz0, cz1 = max(z, of.zb), min(z + hrow, of.zt)
                    if cx1 > cx0 + EPS and cz1 > cz0 + EPS:
                        cut.append((round(cx0, 1), round(cx1, 1), round(cz0, 1), round(cz1, 1)))
                        if cx1 - cx0 >= wcol - EPS and cz1 - cz0 >= hrow - EPS:
                            full_void = True
                if not full_void:
                    n += 1
                    area = (wcol * hrow - sum((c[1] - c[0]) * (c[3] - c[2]) for c in cut)) / 1e6
                    sheets.append(Sheet(id=f"{panel_id}-SH{n:02d}", item=sheet_item, parent=panel_id,
                                        x0=round(x, 1), x1=round(x + wcol, 1), z0=round(z, 1),
                                        z1=round(z + hrow, 1), cutouts=cut, area_m2=round(area, 4)))
        ctx.sheets += sheets

    # 11. conexões e ferragens
    _connect_panel(members, ctx)
    Aa = ctx.rules.data["anchorage"]["base"]
    for m in members:
        if m.role == "BOTTOM_PLATE":
            Lb = m.cut_length
            nA = 1 if Lb <= 2 * Aa["max_from_plate_end"] else math.ceil((Lb - 2 * Aa["max_from_plate_end"]) / Aa["pitch"]) + 1
            ctx.hw(Aa["item"], nA, f"{panel_id} ancoragem da base")

    # 12. painel
    wsheet = sum(s_.area_m2 * ctx.cat.get(s_.item)["thickness"] / 1000 * ctx.cat.get(s_.item).get("density_kg_m3", 600)
                 for s_ in sheets)
    weight = sum(m.weight_kg for m in members) + wsheet
    sig = hashlib.sha1(repr(sorted((m.role, m.item, m.x0, m.x1, m.z0, m.z1, m.plies) for m in members)).encode()
                       + ctx.rules.digest.encode()).hexdigest()[:12]
    org = wf.to_global(xs)
    ctx.panels.append(Panel(id=panel_id, wall=w.id, level=w.level, system=ctx.system, wall_type=wf.wtype,
                            x_start=round(xs, 2), length=round(xe - xs, 2), height=wf.panel_height,
                            origin=(round(org[0], 2), round(org[1], 2), wf.elevation),
                            direction=(round(wf.dirv[0], 6), round(wf.dirv[1], 6)),
                            weight_kg=round(weight, 1), signature=sig, member_ids=[m.id for m in members],
                            sheet_ids=[s_.id for s_ in sheets], braced=wf.braced,
                            special=any(m.special for m in members),
                            clip_start=[list(p_) for p_ in wf.junc.start.clip] if xs < EPS and wf.junc.start.clip else None,
                            clip_end=[list(p_) for p_ in wf.junc.end.clip] if xe > wf.L - EPS and wf.junc.end.clip else None,
                            depth=wf.depth, exterior=w.exterior,
                            openings=[{"id": of.op.id, "kind": of.op.kind, "door": of.door, "x0": round(of.xl - xs, 1),
                                       "x1": round(of.xr - xs, 1), "z0": round(of.zb, 1), "z1": round(of.zt, 1)}
                                      for of in ops]))
    Pl = ctx.rules.data["panels"]
    max_len = min(Pl["max_length"], max(ctx.cat.stock_lengths(wf.plate)))
    if xe - xs > max_len + EPS:
        ctx.issue("V-002", "error", panel_id, f"painel com {xe - xs:.0f} mm acima do limite {max_len:.0f}")
    if weight > Pl["max_weight_kg"]:
        ctx.issue("V-003", "warning", panel_id, f"painel pesa {weight:.0f} kg (limite {Pl['max_weight_kg']} kg)")


def _movable(r) -> bool:
    return r.role in MOVABLE and not getattr(r, "fixed", False)


def _tidy_line(items: list, smax: float, t: float, barrier) -> None:
    """Elimina vãos livres menores que MIN_CLEAR entre verticais de altura total.

    Ordem de preferência: remover a peça móvel (se o espaçamento continuar dentro do
    máximo), encostá-la na vizinha, ou afastá-la até o vão mínimo.
    """
    for _ in range(200):
        items.sort(key=lambda r: r.c)
        changed = False
        for i in range(len(items) - 1):
            a, b = items[i], items[i + 1]
            gap = b.x0 - a.x1
            if not (CLASH < gap < MIN_CLEAR):
                continue
            prev = items[i - 1] if i > 0 else None
            nxt = items[i + 2] if i + 2 < len(items) else None
            # 1) remover
            if _movable(b) and nxt is not None and (barrier(a, nxt) or nxt.c - a.c <= smax + EPS):
                items.pop(i + 1)
                changed = True
                break
            if _movable(a) and prev is not None and (barrier(prev, b) or b.c - prev.c <= smax + EPS):
                items.pop(i)
                changed = True
                break
            # 2) encostar
            if _movable(b) and (nxt is None or nxt.c - (b.c - gap) <= smax + EPS):
                b.x0 -= gap
                b.x1 -= gap
                b.note = (b.note + "; " if b.note else "") + "encostado na peça vizinha"
                changed = True
                break
            if _movable(a) and (prev is None or (a.c + gap) - prev.c <= smax + EPS):
                a.x0 += gap
                a.x1 += gap
                a.note = (a.note + "; " if a.note else "") + "encostado na peça vizinha"
                changed = True
                break
            # 3) afastar até o vão mínimo
            mv = MIN_CLEAR - gap
            if _movable(b) and nxt is not None and nxt.x0 - (b.x1 + mv) >= MIN_CLEAR - EPS \
                    and nxt.c - (b.c + mv) <= smax + EPS:
                b.x0 += mv
                b.x1 += mv
                changed = True
                break
            if _movable(a) and prev is not None and (a.x0 - mv) - prev.x1 >= MIN_CLEAR - EPS \
                    and (a.c - mv) - prev.c <= smax + EPS:
                a.x0 -= mv
                a.x1 -= mv
                changed = True
                break
        if not changed:
            return


def _tidy_centers(cs: list, lo: float, hi: float, smax: float, t: float, keep=()) -> list:
    """Mesma regra para os montantes curtos (cripples) entre dois apoios fixos."""
    cs = sorted(cs)
    keep = set(round(k, 1) for k in keep)
    for _ in range(200):
        chain = [lo] + cs + [hi]
        changed = False
        for i in range(len(chain) - 1):
            a, b = chain[i], chain[i + 1]
            gap = b - a - t
            if not (CLASH < gap < MIN_CLEAR):
                continue
            # índices móveis em cs: i-1 (a) e i (b) quando não são os extremos
            for j, other_nb in ((i, chain[i + 2] if i + 2 < len(chain) else None), (i - 1, chain[i - 1] if i - 1 >= 0 else None)):
                if 0 <= j < len(cs) and round(cs[j], 1) not in keep and other_nb is not None:
                    fixed_side = a if j == i else b
                    if abs(other_nb - fixed_side) <= smax + EPS:
                        cs.pop(j)
                        changed = True
                        break
            if changed:
                break
            if 0 <= i < len(cs) and b != hi:                     # encostar b em a
                nxt = chain[i + 2]
                if nxt - (b - gap) <= smax + EPS:
                    cs[i] = b - gap
                    changed = True
                    break
            if 0 <= i - 1 < len(cs) and a != lo:                 # encostar a em b
                prv = chain[i - 1]
                if (a + gap) - prv <= smax + EPS:
                    cs[i - 1] = a + gap
                    changed = True
                    break
            mv = MIN_CLEAR - gap                                  # afastar até o vão mínimo
            if 0 <= i < len(cs) and b != hi and round(b, 1) not in keep:
                nxt = chain[i + 2]
                if nxt - (b + mv) <= smax + EPS and nxt - (b + mv) - t >= MIN_CLEAR - EPS:
                    cs[i] = b + mv
                    changed = True
                    break
            if 0 <= i - 1 < len(cs) and a != lo and round(a, 1) not in keep:
                prv = chain[i - 1]
                if (a - mv) - prv <= smax + EPS and (a - mv) - prv - t >= MIN_CLEAR - EPS:
                    cs[i - 1] = a - mv
                    changed = True
                    break
        if not changed:
            break
    return cs


def _covered(rects, x, z):
    return any(r.plane == "core" and r.orient in ("V", "H") and r.x0 - 0.5 <= x <= r.x1 + 0.5
               and r.z0 - 0.5 <= z <= r.z1 + 0.5 for r in rects)


def _edge_ok(rects, ops, e, H):
    """A junta vertical em x=e tem apoio dos dois lados em toda a altura (vão da abertura dispensa)."""
    z = 5.0
    while z < H - 4:
        for xp in (e - 9, e + 9):
            if any(of.xl < xp < of.xr and of.zb < z < of.zt for of in ops):
                continue
            if not _covered(rects, xp, z):
                return False
        z += 20.0
    return True


def _sheet_columns(rects, ops, xs, xe, W, H):
    """Escolhe as juntas verticais sobre o eixo de montantes existentes (placa cortada se preciso)."""
    cands = sorted({round((r.x0 + r.x1) / 2, 2) for r in rects if r.orient == "V" and r.plane == "core"})
    ok = [c for c in cands if xs + 150 < c < xe - 150 and _edge_ok(rects, ops, c, H)]
    cols, fallback = [xs], []
    cur = xs
    while xe - cur > W + EPS:
        window = [c for c in ok if cur + 300 <= c <= cur + W + EPS and (xe - c >= 300 or xe - c <= EPS)]
        if window:
            nxt = max(window)
        else:
            nxt = cur + W
            fallback.append(nxt)
        cols.append(nxt)
        cur = nxt
    cols.append(xe)
    return cols, fallback


def _sheet_rows(rects, H, SH, t, z1s):
    """Junta horizontal embaixo ou em cima: a que ficar mais longe de vergas e peitoris."""
    if H <= SH + EPS:
        return [0.0, H]
    return [0.0, float(SH), H]             # junta sempre a 2400 do piso, sobre a linha fixa de bloqueio
    hz = [(r.z0, r.z1) for r in rects if r.role in ("HEADER", "SILL", "PACKER")]

    def conflict(z):
        return sum(1 for z0, z1 in hz if z0 - MIN_CLEAR - t < z < z1 + MIN_CLEAR + t)
    top_joint, low_joint = SH, H - SH
    if conflict(low_joint) <= conflict(top_joint) and low_joint > 150:
        return [0.0, low_joint, H]
    return [0.0, top_joint, H]


def sheet_edges(wf, xs, xe, W, t):
    sg0 = wf.grid_from(W)
    e = sg0 + math.floor((xs - sg0) / W) * W
    while e <= xs + t:
        e += W
    out = []
    while e < xe - t:
        out.append(e)
        e += W
    return out


def _edge_support(rects, edges, ops, z0s, z1s, stud, t, xs, xe, ctx, w, pi):
    step = 10.0

    def covered(x, z):
        return any(r.plane == "core" and r.orient in ("V", "H") and r.x0 - 0.5 <= x <= r.x1 + 0.5
                   and r.z0 - 0.5 <= z <= r.z1 + 0.5 for r in rects)

    def in_void(x, z):
        return any(of.xl < x < of.xr and of.zb < z < of.zt for of in ops)

    for e in edges:
        for side, xp, (a0, a1) in ((-1, e - 9, (e - t, e)), (1, e + 9, (e, e + t))):
            z = z0s + step / 2
            runs, cur = [], None
            while z < z1s:
                bad = not covered(xp, z) and not in_void(xp, z)
                if bad and cur is None:
                    cur = [z, z]
                elif bad:
                    cur[1] = z
                elif cur is not None:
                    runs.append(cur)
                    cur = None
                z += step
            if cur is not None:
                runs.append(cur)
            for lo, hi in runs:
                # apoia de uma peça horizontal (ou placa) abaixo até outra acima
                below = [r for r in rects if r.x0 - 0.5 <= xp <= r.x1 + 0.5 and r.z1 <= lo + 0.5 and r.orient in ("H", "V")]
                above = [r for r in rects if r.x0 - 0.5 <= xp <= r.x1 + 0.5 and r.z0 >= hi - 0.5 and r.orient in ("H", "V")]
                zb = max((r.z1 for r in below), default=z0s)
                zt = min((r.z0 for r in above), default=z1s)
                cands = [(e - t / 2, e + t / 2)]
                for r in list(rects):            # encostar na face da peça vizinha
                    if r.orient == "V" and r.plane == "core" and abs((r.x0 + r.x1) / 2 - e) < 2 * t:
                        cands += [(r.x1, r.x1 + t), (r.x0 - t, r.x0)]
                cands.append((a0, a1))
                both = [c for c in cands if c[0] <= e - 9 and c[1] >= e + 9]
                one = [c for c in cands if c not in both and c[0] <= xp <= c[1]]
                cands = sorted(set(both), key=lambda c: abs((c[0] + c[1]) / 2 - e)) + one
                for x0, x1 in cands:
                    if x0 < xs - EPS or x1 > xe + EPS:
                        continue
                    if any(r.plane == "core" and r.orient == "V" and r.z0 < zt - 1 and r.z1 > zb + 1 and
                           (CLASH < x0 - r.x1 < MIN_CLEAR or CLASH < r.x0 - x1 < MIN_CLEAR) for r in rects):
                        continue
                    if any(r.plane == "core" and r.orient in ("V", "H", "P") and x0 < r.x1 - CLASH and x1 > r.x0 + CLASH
                           and zb < r.z1 - CLASH and zt > r.z0 + CLASH for r in rects):
                        continue
                    if any(of.xl < (x0 + x1) / 2 < of.xr and of.zb < (zb + zt) / 2 < of.zt for of in ops):
                        continue
                    role = "SHEET_STUD" if zb <= z0s + 1 and zt >= z1s - 1 else "NAILER"
                    rects.append(R(role, x0, x1, zb, zt, stud, rule="sheathing.edge_support",
                                   note="apoio da junta da placa estrutural"))
                    break
                else:
                    ctx.issue("V-062", "warning", f"{w.id}/PN{pi:02d}",
                              f"junta de placa em x={e - xs:.0f} sem espaço para apoio entre z={zb:.0f} e {zt:.0f}")


def _strap_x(wf: WallFrame, ctx: Ctx, rects: list[R], xs: float, xe: float, ops):
    B = ctx.rules.data["bracing"]
    sx = B["strap_x"]
    width = ctx.cat.face(sx["item"])
    segs = _free_segments(xs, xe, [(of.zone_l, of.zone_r) for of in ops], wf.t)
    Hb = wf.z_stud1 - wf.z_stud0
    amin, amax = math.radians(sx["angle_min"]), math.radians(sx["angle_max"])
    for a, b in segs:
        Ls = b - a
        if Ls < B["min_segment_length"]:
            continue
        n = max(1, math.ceil(Ls * math.tan(amin) / Hb - 1e-9))
        ang = math.atan(Hb * n / Ls)
        if ang > amax + 1e-6:
            continue
        bay = Ls / n
        for i in range(n):
            x0, x1 = a + i * bay, a + (i + 1) * bay
            for (p0, p1) in (((x0, wf.z_stud0), (x1, wf.z_stud1)), ((x0, wf.z_stud1), (x1, wf.z_stud0))):
                d = g.unit(g.sub(p1, p0))
                nrm = (-d[1] * width / 2, d[0] * width / 2)
                poly = [g.add(p0, nrm), g.add(p1, nrm), g.sub(p1, nrm), g.sub(p0, nrm)]
                Ld = g.dist(p0, p1)
                rects.append(R("BRACE_STRAP", x0, x1, wf.z_stud0, wf.z_stud1, sx["item"], "A", plane="face",
                               polygon=poly, cut=round(Ld + 2 * 150, 1), rule="bracing.strap_x",
                               note=f"fita em X a {math.degrees(ang):.1f}°"))
        ctx.hw(sx["gusset"], 4 * n, f"{wf.wall.id} gussets da fita em X")


def _free_segments(xs, xe, zones, t):
    segs, x = [], xs + t
    for zl, zr in sorted(zones):
        if zl > x:
            segs.append((x, min(zl, xe - t)))
        x = max(x, zr)
    if xe - t > x:
        segs.append((x, xe - t))
    return [(a, b) for a, b in segs if b - a > 1]


def _bracing_segments(wf: WallFrame, ctx: Ctx):
    """Método segmentado (A5.3): trechos de altura total sem aberturas, com placa ou fita."""
    if not wf.braced:
        return
    B = ctx.rules.data["bracing"]
    has_sheet = bool(wf.wt.get("sheathing"))
    if not has_sheet and not (ctx.system == "steel" and B.get("strap_x")):
        return
    zones = [(of.zone_l, of.zone_r) for of in wf.openings]
    segs = _free_segments(0, wf.L, zones, 0)
    total = 0.0
    for a, b in segs:
        Ls = b - a
        if Ls >= B["min_segment_length"]:
            total += Ls
            ctx.hw(B["hold_down"]["item"], 2, f"{wf.wall.id} hold-downs do segmento {a:.0f}-{b:.0f}")
    ctx.braced_segments.append((wf.wall.level, wf.axis, total, wf.wall.id))


def _cap_plates(wf: WallFrame, ctx: Ctx):
    """Placa de capa (2ª placa superior) com juntas desencontradas das juntas de painel (A10.2)."""
    lap = ctx.rules.data["plates"]["cap_lap_min"]
    stock = max(ctx.cat.stock_lengths(wf.plate))
    a, b = 0.0, wf.L
    js, je = wf.junc.start, wf.junc.end
    if js.kind == "through":
        a += js.other_depth
    elif js.kind in ("butt", "tee"):
        a -= js.other_depth
    if je.kind == "through":
        b -= je.other_depth
    elif je.kind in ("butt", "tee"):
        b += je.other_depth
    intervals = [(a, b)]
    for tp, tw, _ in wf.tees:
        new = []
        for x0, x1 in intervals:
            if x0 < tp - tw / 2 < x1:
                new += [(x0, tp - tw / 2), (tp + tw / 2, x1)]
            else:
                new.append((x0, x1))
        intervals = new
    pjoints = [p[1] for p in wf.panels[:-1]]
    pieces = []
    for x0, x1 in intervals:
        start = x0
        while x1 - start > stock + EPS:
            cut = start + stock
            while any(abs(cut - j) < lap for j in pjoints) and cut > start + 600:
                cut -= 50
            pieces.append((start, cut))
            start = cut
        pieces.append((start, x1))
    z0 = wf.H - wf.pt
    wall_id = f"{ctx.pfx}-{wf.wall.level}-{wf.wall.id}"
    for i, (x0, x1) in enumerate(pieces, start=1):
        m = ctx.new_member("CAP_PLATE", wf.plate, wf.wall.level, "wall", wall_id, frame="wall",
                           x0=round(x0, 2), x1=round(x1, 2), z0=z0, z1=wf.H, orientation="H",
                           rule="plates.cap_lap_min", note="montagem em obra: sobrepõe as juntas de painel")
        m.id = f"{wall_id}-CAP-{i:02d}"
        ctx.members.append(m)
        conn = ctx.rules.connection("LG-03")
        ctx.hw(conn.get("fastener", "definir"), qty_for(conn, x1 - x0), f"{m.id} capa-placa")
    for j in pjoints:
        cover = [(x0, x1) for x0, x1 in pieces if x0 <= j <= x1]
        best = max((min(j - x0, x1 - j) for x0, x1 in cover), default=0)
        if best < lap - EPS:
            ctx.issue("V-065", "error", wall_id, f"junta de painel em x={j:.0f} com transpasse da capa de {best:.0f} mm (mín. {lap})")


def _assign_ids(members: list[Member], panel_id: str):
    groups: dict[tuple, list[Member]] = {}
    for m in members:
        groups.setdefault((m.opening or "", m.role), []).append(m)
    for (op, role), ms in groups.items():
        ms.sort(key=lambda m: (round(m.x0, 1), round(m.z0, 1)))
        for i, m in enumerate(ms, start=1):
            m.id = f"{panel_id}-{op + '-' if op else ''}{role}-{i:02d}"


def _conn_type(ra: str, rb: str) -> str:
    pair = {ra, rb}
    if "BRACE_STRAP" in pair or "STRAP" in pair:
        return "LG-17"
    if "BOTTOM_PLATE" in pair:
        return "LG-01" if (pair - {"BOTTOM_PLATE"}) & VERTICAL else "LG-16"
    if "TOP_PLATE" in pair:
        return "LG-02" if (pair - {"TOP_PLATE"}) & VERTICAL else "LG-05"
    if "HEADER" in pair:
        return "LG-05"
    if "SILL" in pair or "PACKER" in pair or "ARCH_FILLER" in pair:
        return "LG-16"
    if "BLOCK" in pair:
        return "LG-15"
    return "LG-04"


def _conn(ctx, a, b, code, conn, contact_len):
    ctx._seq += 1
    return Connection(id=f"C{ctx._seq}", a=a, b=b, type=code, fastener=conn.get("fastener", "definir"),
                      qty=qty_for(conn, contact_len))


def contact(a: Member, b: Member) -> tuple[str, float]:
    """Retorna ('touch'|'clash'|'none', comprimento de contato)."""
    gx = max(a.x0, b.x0) - min(a.x1, b.x1)
    gz = max(a.z0, b.z0) - min(a.z1, b.z1)
    if gx < -CLASH and gz < -CLASH:
        return "clash", 0.0
    if -CLASH <= gx <= TOUCH and gz < -CLASH:
        return "touch", -gz
    if -CLASH <= gz <= TOUCH and gx < -CLASH:
        return "touch", -gx
    return "none", 0.0


def _connect_panel(members: list[Member], ctx: Ctx):
    core = [m for m in members if m.plane == "core"]
    face = [m for m in members if m.plane == "face"]
    for i, a in enumerate(core):
        for b in core[i + 1:]:
            if a.orientation == "P" or b.orientation == "P":
                if a.x0 <= b.x1 + TOUCH and b.x0 <= a.x1 + TOUCH and a.z0 <= b.z1 + TOUCH and b.z0 <= a.z1 + TOUCH:
                    code = "LG-16"
                    ctx.connections.append(_conn(ctx, a.id, b.id, code, ctx.rules.connection(code), 100))
                continue
            kind, clen = contact(a, b)
            if kind == "touch":
                code = _conn_type(a.role, b.role)
                ctx.connections.append(_conn(ctx, a.id, b.id, code, ctx.rules.connection(code), clen))
    for f in face:
        for c in core:
            if c.orientation == "V" and f.orientation == "H":
                if c.x0 < f.x1 and c.x1 > f.x0 and c.z0 <= f.z0 and c.z1 >= f.z1:
                    ctx.connections.append(_conn(ctx, f.id, c.id, "LG-17", ctx.rules.connection("LG-17"), 40))
            elif f.orientation == "A" and c.role in ("BOTTOM_PLATE", "TOP_PLATE", "STUD_END", "STUD"):
                if c.x0 < f.x1 and c.x1 > f.x0:
                    ctx.connections.append(_conn(ctx, f.id, c.id, "LG-17", ctx.rules.connection("LG-17"), 40))
