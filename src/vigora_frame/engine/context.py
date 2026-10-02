"""Contexto compartilhado de uma execução: regras, catálogo, coleta de saídas."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

from ..config import Catalog, Rules
from ..model import Connection, Hardware, Issue, Member, Panel, Project, Sheet, TrussMark


@dataclass
class Ctx:
    project: Project
    rules: Rules
    cat: Catalog
    members: list[Member] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    sheets: list[Sheet] = field(default_factory=list)
    panels: list[Panel] = field(default_factory=list)
    hardware: list[Hardware] = field(default_factory=list)
    trusses: list[TrussMark] = field(default_factory=list)
    stairs: list = field(default_factory=list)
    roof_info: dict = field(default_factory=dict)
    wall_upper: dict = field(default_factory=dict)
    post_lines: dict = field(default_factory=dict)     # linhas de pilares já criadas (varandas)
    tank_zones: list = field(default_factory=list)     # envelopes de caixa d'água (o telhado desvia)
    tanks: list = field(default_factory=list)        # parede -> altura do painel de complemento
    issues: list[Issue] = field(default_factory=list)
    # dados para verificações cruzadas
    wall_frames: dict = field(default_factory=dict)          # id -> WallFrame
    stud_lines: dict = field(default_factory=lambda: defaultdict(list))   # wall id -> centros globais (x,y)
    bearing_points: list = field(default_factory=list)        # (tipo, id, ponto global, nível)
    braced_segments: list = field(default_factory=list)       # (nível, eixo, comprimento, parede)
    panel_ros: dict = field(default_factory=dict)             # painel -> vãos (xl, xr, zb, zt) locais
    panel_bands: dict = field(default_factory=dict)
    placements: dict = field(default_factory=dict)            # treliça/piso -> posição global           # painel -> (z_stud0, z_stud1)
    _seq: int = 0

    @property
    def system(self) -> str:
        return self.rules.system

    @property
    def pfx(self) -> str:
        return self.project.id

    def issue(self, code: str, severity: str, element: str, message: str):
        self.issues.append(Issue(code=code, severity=severity, element=element, message=message))

    def hw(self, item: str, qty: float, source: str, unit: str = "un"):
        if qty > 0:
            self.hardware.append(Hardware(item=item, qty=qty, unit=unit, source=source))

    def kg(self, item: str, length_mm: float, plies: int = 1) -> float:
        try:
            return self.cat.kg_per_m(item) * length_mm / 1000.0 * plies
        except Exception:
            return 0.0

    def new_member(self, role: str, item: str, level: str, group: str, parent: str, **kw) -> Member:
        """Cria a peça. O id definitivo é atribuído depois (numeração estável)."""
        self._seq += 1
        m = Member(id=f"tmp{self._seq}", role=role, item=item, system=self.system, level=level,
                   group=group, parent=parent, **kw)
        if not m.cut_length:
            if m.orientation == "V":
                m.cut_length = round(m.z1 - m.z0, 1)
            elif m.orientation == "H":
                m.cut_length = round(m.x1 - m.x0, 1)
        m.weight_kg = round(self.kg(item, m.cut_length, m.plies), 3)
        try:
            m.depth = self.cat.depth(item) if m.frame in ("panel", "wall", "plan") else self.cat.face(item)
        except Exception:
            m.depth = 0.0
        return m


def qty_for(conn: dict, contact_len: float) -> int:
    if "qty_per_m" in conn:
        return max(1, math.ceil(conn["qty_per_m"] * contact_len / 1000.0))
    return int(conn.get("qty", 0))
