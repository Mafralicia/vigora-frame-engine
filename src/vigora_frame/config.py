"""Catálogo, ruleset e tabelas (Anexo A2, seção 6.5)."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
STEEL_DENSITY = 7850.0  # kg/m³


class ConfigError(Exception):
    pass


@dataclass
class Catalog:
    items: dict[str, dict]
    version: str

    @classmethod
    def load(cls, root: Path = ROOT) -> "Catalog":
        items: dict[str, dict] = {}
        versions = []
        for name in ("profiles.yaml", "fasteners.yaml"):
            data = yaml.safe_load((root / "catalog" / name).read_text(encoding="utf-8"))
            versions.append(data.get("version", "?"))
            for it in data["items"]:
                if it["id"] in items:
                    raise ConfigError(f"item duplicado no catálogo: {it['id']}")
                cls._validate_item(it)
                items[it["id"]] = it
        return cls(items=items, version="+".join(versions))

    @staticmethod
    def _validate_item(it: dict) -> None:
        req = ["id", "system", "category"]
        for k in req:
            if k not in it:
                raise ConfigError(f"item sem campo obrigatório '{k}': {it}")
        cat = it["category"]
        if cat in ("lumber", "engineered", "column") and it["system"] == "wood":
            for k in ("face", "depth", "stock_lengths"):
                if k not in it:
                    raise ConfigError(f"{it['id']}: campo '{k}' obrigatório")
        if it["system"] == "steel" and cat in ("stud", "track", "joist", "strap"):
            for k in ("web", "flange", "thickness", "stock_lengths"):
                if k not in it:
                    raise ConfigError(f"{it['id']}: campo '{k}' obrigatório")
            if it["thickness"] <= 0 or it["web"] <= 0:
                raise ConfigError(f"{it['id']}: dimensões inválidas")

    def get(self, item_id: str) -> dict:
        if item_id not in self.items:
            raise ConfigError(f"item não cadastrado no catálogo: {item_id}")
        return self.items[item_id]

    def face(self, item_id: str) -> float:
        """Largura da peça vista em elevação (madeira: espessura; aço: mesa)."""
        it = self.get(item_id)
        if it["system"] == "steel":
            if it.get("shape") == "flat":
                return float(it["web"])
            return float(it["flange"])
        return float(it["face"])

    def depth(self, item_id: str) -> float:
        """Dimensão na espessura da parede / altura da viga."""
        it = self.get(item_id)
        if it["system"] == "steel":
            return float(it["web"])
        return float(it["depth"])

    def thickness(self, item_id: str) -> float:
        it = self.get(item_id)
        return float(it.get("thickness", it.get("face", 0)))

    def kg_per_m(self, item_id: str) -> float:
        it = self.get(item_id)
        if it["system"] == "steel" or it.get("shape"):
            t = it["thickness"]
            developed = it["web"] + 2 * it.get("flange", 0) + 2 * it.get("lip", 0)
            return developed * t * 1e-6 * STEEL_DENSITY
        dens = it.get("density_kg_m3", 500)
        return it["face"] * it["depth"] * 1e-6 * dens

    def stock_lengths(self, item_id: str) -> list[float]:
        return sorted(float(x) for x in self.get(item_id).get("stock_lengths", []))

    def is_approved(self, item_id: str) -> bool:
        it = self.get(item_id)
        if not it.get("approved_by"):
            return False
        return "definir" not in json.dumps(it)


@dataclass
class HeaderRow:
    load_case: str
    span_max: float
    item: str
    plies: int
    jack_per_side: int
    king_per_side: int


@dataclass
class Rules:
    data: dict[str, Any]
    headers: list[HeaderRow]
    limits: dict[str, Any]
    path: Path
    digest: str = ""
    extra: dict = field(default_factory=dict)

    @classmethod
    def load(cls, name: str, root: Path = ROOT) -> "Rules":
        p = root / "rules" / (name if name.endswith(".yaml") else f"{name}.yaml")
        if not p.exists():
            raise ConfigError(f"ruleset não encontrado: {p}")
        raw = p.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        hp = root / "rules" / data["openings"]["header_table"]
        headers = []
        with open(hp, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                headers.append(HeaderRow(row["load_case"], float(row["span_max_mm"]), row["header_item"],
                                         int(row["plies"]), int(row["jack_per_side"]), int(row["king_per_side"])))
        limits = yaml.safe_load((root / "limits" / "manufacturing.yaml").read_text(encoding="utf-8"))
        digest = hashlib.sha256((raw + hp.read_text(encoding="utf-8")).encode()).hexdigest()[:12]
        return cls(data=data, headers=headers, limits=limits, path=p, digest=digest)

    def __getitem__(self, k):
        return self.data[k]

    @property
    def name(self) -> str:
        return self.data["ruleset"]

    @property
    def system(self) -> str:
        return self.data["system"]

    def approved(self) -> bool:
        ap = self.data.get("approval", {})
        if not ap.get("approved_by"):
            return False
        return all(b.get("approved_by") for b in self.data.get("basis", {}).values())

    def unapproved_rules(self) -> list[str]:
        out = []
        if not self.data.get("approval", {}).get("approved_by"):
            out.append("ruleset (approval)")
        for k, b in self.data.get("basis", {}).items():
            if not b.get("approved_by"):
                out.append(k)
        return out

    def header_for(self, load_case: str, span: float) -> HeaderRow | None:
        rows = sorted([h for h in self.headers if h.load_case == load_case], key=lambda h: h.span_max)
        for h in rows:
            if span <= h.span_max:
                return h
        return None

    def wall_type(self, wall) -> str:
        if wall.wall_type:
            if wall.wall_type not in self.data["wall_types"]:
                raise ConfigError(f"tipo de parede não definido no ruleset: {wall.wall_type}")
            return wall.wall_type
        a = self.data["auto_wall_type"]
        key = ("exterior" if wall.exterior else "interior") + "_" + ("bearing" if wall.bearing else "nonbearing")
        return a[key]

    def connection(self, code: str) -> dict:
        return self.data["connections"].get(code, {"fastener": "definir", "qty": 0})
