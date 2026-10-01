"""Modelo de dados neutro do Vigora Frame Engine (seção 6 da especificação).

Unidades: mm, graus, kg. Coordenadas de planta em mm (x, y); z a partir do nível.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

SCHEMA_VERSION = "0.1"

# ------------------------------------------------------------------ entradas
class Opening(BaseModel):
    id: str
    kind: Literal["window", "door", "arch", "passage"] = "window"
    offset: float = Field(..., description="distância do início do eixo da parede até a lateral esquerda do caixilho")
    width: float
    height: float
    sill: float = 0.0          # altura do peitoril a partir da base da parede (0 para portas)
    rise: float = 0.0          # flecha do arco (kind = arch)
    opening_type: Optional[str] = None   # AB-01 ... (informativo)


class Wall(BaseModel):  # noqa: D101
    id: str
    level: str
    start: tuple[float, float]
    end: tuple[float, float]
    thickness: Optional[float] = None    # se None, usa a profundidade do montante do tipo
    height: float
    exterior: bool = True
    bearing: bool = True
    wall_type: Optional[str] = None
    braced: Optional[bool] = None        # parede de contraventamento (default: externas)
    openings: list[Opening] = []
    # preenchido para facetas de parede curva
    facet_of: Optional[str] = None
    miter_start: float = 0.0             # ângulo de meia-esquadria (graus) na ponta inicial
    miter_end: float = 0.0


class CurvedWall(BaseModel):
    id: str
    level: str
    center: tuple[float, float]
    radius: float
    angle_start: float                   # graus
    angle_end: float
    height: float
    exterior: bool = True
    bearing: bool = False
    wall_type: Optional[str] = None


class Level(BaseModel):
    id: str
    name: str
    elevation: float
    height: float


class FloorSpec(BaseModel):
    id: str
    level: str                           # pavimento que o piso sustenta (piso do nível)
    outline: list[tuple[float, float]]   # polígono externo (face externa das paredes)
    holes: list[list[tuple[float, float]]] = []
    joist_direction: Literal["x", "y"] = "y"


class RoofSpec(BaseModel):
    id: str
    level: str                           # nível das paredes que recebem a cobertura
    kind: Literal["gable", "mono", "hip"] = "gable"
    ridge_axis: Literal["x", "y"] = "x"      # direção da cumeeira (treliças distribuídas nessa direção)
    pitch_deg: float = 25.0
    ends: tuple[str, str] = ("gable", "gable")   # gable (oitão) | abut (encostado) | valley (rincão sobre outro telhado)
    support: Literal["walls", "high_wall", "parapet"] = "walls"   # apoio: paredes | parede alta | platibanda
    bearing_height: Optional[float] = None       # platibanda: altura do banzo inferior (mm do piso do nível)
    parapet_min: float = 200.0                   # platibanda: altura mínima da mureta acima do telhado
    high_side: Literal["start", "end"] = "end"   # meia-água: lado alto no início ou no fim do vão
    girder_setback: Optional[float] = None       # 4 águas: distância da treliça mestra à parede de topo
    overhang: Optional[float] = None
    spacing: Optional[float] = None
    truss_type: Optional[str] = None     # força um tipo (fink, howe, kingpost, pratt)
    outline: Optional[list[tuple[float, float]]] = None   # retângulo externo; default = bbox das paredes


class ColumnSpec(BaseModel):
    id: str
    level: str
    position: tuple[float, float]
    height: float
    tributary_area_m2: float
    load_kPa: Optional[float] = None


class StairSpec(BaseModel):
    id: str
    level: str                            # pavimento de chegada (o piso que tem o vão)
    start: tuple[float, float]            # centro do primeiro espelho, no piso de baixo
    direction: Literal["+x", "-x", "+y", "-y"] = "+y"
    width: float = 900.0
    riser_max: float = 180.0
    tread: Optional[float] = None         # passo; vazio = pela regra de Blondel (2h + b ≈ 635)
    stringer: str = "W-38x286"
    tread_item: str = "W-38x286"


class TankSpec(BaseModel):
    id: str
    model: str = "BR_1000L"                       # chave em catalog/tanks.yaml
    level: str                                    # nível cujo telhado abriga a caixa (ático)
    position: Optional[tuple[float, float]] = None  # centro em planta; vazio = automático
    installation: Literal["attic", "tower"] = "attic"


class Project(BaseModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    name: str
    system: Literal["wood", "steel"]
    ruleset: str
    levels: list[Level]
    walls: list[Wall] = []
    curved_walls: list[CurvedWall] = []
    floors: list[FloorSpec] = []
    roofs: list[RoofSpec] = []
    columns: list[ColumnSpec] = []
    stairs: list[StairSpec] = []
    tanks: list[TankSpec] = []
    meta: dict = {}          # cliente, local, responsável técnico, CREA, ART, verificação, data


# ------------------------------------------------------------------ saídas
class Member(BaseModel):
    id: str
    role: str
    item: str
    system: str
    level: str
    group: str                    # parede, piso, cobertura, pilar
    parent: str                   # id do painel / treliça / piso
    frame: Literal["panel", "plan", "truss", "wall", "stair"] = "panel"
    # geometria no referencial do frame (painel: x ao longo, z vertical)
    x0: float = 0.0
    x1: float = 0.0
    z0: float = 0.0
    z1: float = 0.0
    orientation: Literal["V", "H", "A", "P"] = "V"     # vertical, horizontal, angulada, placa
    polygon: Optional[list[tuple[float, float]]] = None
    cut_length: float = 0.0
    angle_a: float = 90.0         # ângulo de corte (graus) em cada ponta; 90 = reto
    angle_b: float = 90.0
    plies: int = 1
    plane: Literal["core", "face"] = "core"
    special: bool = False
    rule: str = ""
    opening: Optional[str] = None
    note: str = ""
    weight_kg: float = 0.0
    depth: float = 0.0           # dimensão fora do plano do desenho (espessura da parede / altura da viga)


class Connection(BaseModel):
    id: str
    a: str
    b: str
    type: str
    fastener: str
    qty: int


class Sheet(BaseModel):
    id: str
    item: str
    parent: str
    x0: float
    x1: float
    z0: float
    z1: float
    cutouts: list[tuple[float, float, float, float]] = []
    area_m2: float = 0.0


class Panel(BaseModel):
    id: str
    wall: str
    level: str
    system: str
    wall_type: str
    x_start: float                # posição no comprimento de framing da parede
    length: float
    height: float
    origin: tuple[float, float, float]   # ponto global do início do painel
    direction: tuple[float, float]       # vetor unitário ao longo da parede
    weight_kg: float = 0.0
    signature: str = ""
    member_ids: list[str] = []
    sheet_ids: list[str] = []
    braced: bool = False
    special: bool = False
    clip_start: Optional[list] = None    # meia-esquadria: reta (I, O) em planta na ponta inicial
    clip_end: Optional[list] = None
    depth: float = 0.0
    exterior: bool = True
    openings: list[dict] = []            # vãos no referencial do painel: id, tipo, x0, x1, z0, z1


class Issue(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"]
    element: str
    message: str


class Hardware(BaseModel):
    item: str
    qty: float
    unit: str = "un"
    source: str = ""


class TrussMark(BaseModel):
    mark: str
    type: str
    span: float
    rise: float
    pitch_deg: float
    count: int
    member_ids: list[str] = []
    height: float = 0.0


class Result(BaseModel):
    schema_version: str = SCHEMA_VERSION
    project: str
    project_name: str
    system: str
    ruleset: str
    ruleset_approved: bool
    run_id: str
    input_hash: str
    panels: list[Panel] = []
    members: list[Member] = []
    connections: list[Connection] = []
    sheets: list[Sheet] = []
    hardware: list[Hardware] = []
    trusses: list[TrussMark] = []
    issues: list[Issue] = []
    stats: dict = {}
    meta: dict = {}
