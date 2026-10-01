"""Quantitativo e plano de corte (seção 10).

Otimização de barras: best-fit decrescente com kerf, seguido de redução de cada
barra para o menor comprimento comercial que comporta seus cortes.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

from .config import Catalog, Rules
from .model import Result

LINEAR_CATS = {"lumber", "engineered", "stud", "track", "joist", "column", "strap"}


@dataclass
class Bar:
    stock: float
    cuts: list[tuple[str, float]] = field(default_factory=list)

    def used(self, kerf: float) -> float:
        return sum(c[1] for c in self.cuts) + kerf * max(0, len(self.cuts) - 1)


def optimize_cuts(pieces: list[tuple[str, float]], stocks: list[float], kerf: float) -> tuple[list[Bar], list]:
    """pieces: (id, comprimento). Retorna barras e peças que não cabem em nenhuma barra."""
    stocks = sorted(stocks)
    big = stocks[-1]
    bars: list[Bar] = []
    too_long = []
    for pid, L in sorted(pieces, key=lambda p: (-p[1], p[0])):
        if L > big + 1e-6:
            too_long.append((pid, L))
            continue
        best, best_rem = None, None
        for b in bars:
            rem = b.stock - b.used(kerf) - (kerf if b.cuts else 0) - L
            if rem >= -1e-6 and (best_rem is None or rem < best_rem):
                best, best_rem = b, rem
        if best is None:
            best = Bar(big)
            bars.append(best)
        best.cuts.append((pid, L))
    for b in bars:
        need = b.used(kerf)
        for s in stocks:
            if s + 1e-6 >= need:
                b.stock = s
                break
    return bars, too_long


def lower_bound(pieces, big, kerf):
    return math.ceil(sum(L + kerf for _, L in pieces) / (big + kerf))


def quantities(res: Result, cat: Catalog, rules: Rules) -> dict:
    kerf = rules.data["manufacturing"]["kerf"]
    reuse = rules.data["manufacturing"]["offcut_min_reusable"]
    rows = []                      # lista de peças (BOM)
    by_item = defaultdict(list)
    for m in res.members:
        it = cat.get(m.item)
        for k in range(m.plies):
            rows.append(m)
            if it["category"] in LINEAR_CATS and not m.special:
                by_item[m.item].append((m.id if m.plies == 1 else f"{m.id}#{k + 1}", m.cut_length))
    cut_plan = {}
    consolidated = []
    for item, pieces in sorted(by_item.items()):
        stocks = cat.stock_lengths(item)
        bars, too_long = optimize_cuts(pieces, stocks, kerf)
        total_cut = sum(L for _, L in pieces if L <= max(stocks) + 1e-6)
        total_bar = sum(b.stock for b in bars)
        offcuts = [b.stock - b.used(kerf) for b in bars]
        cut_plan[item] = {"bars": bars, "too_long": too_long, "lb": lower_bound(pieces, max(stocks), kerf)}
        bar_count = defaultdict(int)
        for b in bars:
            bar_count[b.stock] += 1
        consolidated.append({
            "item": item, "category": cat.get(item)["category"], "pieces": len(pieces),
            "cut_m": round(total_cut / 1000, 2), "bars": dict(sorted(bar_count.items())), "bars_total": len(bars),
            "bar_m": round(total_bar / 1000, 2), "yield": round(total_cut / total_bar, 4) if total_bar else 0,
            "reusable_offcuts": sum(1 for o in offcuts if o >= reuse),
            "kg": round(cat.kg_per_m(item) * total_bar / 1000, 1),
            "lower_bound_bars": cut_plan[item]["lb"],
        })
    # peças especiais (CNC)
    specials = [m for m in res.members if m.special]
    # placas
    sheets = defaultdict(lambda: {"count": 0, "area": 0.0, "net": 0.0})
    for s in res.sheets:
        W, H = cat.get(s.item)["size"]
        d = sheets[s.item]
        d["count"] += 1
        d["area"] += (s.x1 - s.x0) * (s.z1 - s.z0) / 1e6
        d["net"] += s.area_m2
    sheet_rows = []
    for item, d in sorted(sheets.items()):
        W, H = cat.get(item)["size"]
        full = W * H / 1e6
        # aproveitamento de sobras entre placas parciais: estimativa por área + 10% de perda de corte
        est = math.ceil(d["area"] / full * 1.10)
        sheet_rows.append({"item": item, "positions": d["count"], "area_m2": round(d["area"], 2),
                           "net_m2": round(d["net"], 2), "sheets_to_buy": max(est, math.ceil(d["area"] / full))})
    # fixadores de fechamento (paredes)
    hw = defaultdict(float)
    for h in res.hardware:
        hw[(h.item, h.unit)] += h.qty
    for c in res.connections:
        hw[(c.fastener, "un")] += c.qty
    fasten = rules.data["sheathing"]["fastening"]
    wall_sheets = [s for s in res.sheets if "-SH" in s.id]
    for s in wall_sheets:
        w_, h_ = s.x1 - s.x0, s.z1 - s.z0
        edge = 2 * (w_ + h_) / fasten["edge_pitch"]
        field_ = max(0, (w_ / 400 - 1)) * h_ / fasten["field_pitch"]
        hw[(fasten["fastener"], "un")] += math.ceil(edge + field_)
    hardware_rows = []
    for (item, unit), q in sorted(hw.items()):
        waste = cat.get(item).get("waste", 0) if item in cat.items else 0
        hardware_rows.append({"item": item, "unit": unit, "qty": math.ceil(q), "waste": waste,
                              "qty_buy": math.ceil(q * (1 + waste))})
    panels = [{"id": p.id, "wall": p.wall, "level": p.level, "type": p.wall_type, "length": p.length,
               "height": p.height, "weight_kg": p.weight_kg, "members": len(p.member_ids),
               "sheets": len(p.sheet_ids), "signature": p.signature, "special": p.special} for p in res.panels]
    total_kg = sum(r["kg"] for r in consolidated)
    return {"consolidated": consolidated, "cut_plan": cut_plan, "sheets": sheet_rows, "hardware": hardware_rows,
            "specials": specials, "panels": panels, "bom_rows": len(rows),
            "summary": {"linear_m": round(sum(r["cut_m"] for r in consolidated), 1),
                        "bars": sum(r["bars_total"] for r in consolidated),
                        "yield": round(sum(r["cut_m"] for r in consolidated) / max(1e-9, sum(r["bar_m"] for r in consolidated)), 4),
                        "kg_linear": round(total_kg, 1),
                        "sheets": sum(r["sheets_to_buy"] for r in sheet_rows)}}
