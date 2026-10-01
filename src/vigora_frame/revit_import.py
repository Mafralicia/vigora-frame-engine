"""Tradução do modelo bruto do Revit para o projeto do motor (roda em CPython, testável fora do Revit).

O plugin (IronPython, dentro do Revit) só extrai dados brutos em mm (paredes, aberturas, níveis, telhados,
pisos, escadas, caixas) e a configuração do projeto (arquivo `<modelo>.vigora.json` ao lado do .rvt).
Aqui fica a inteligência: eixo das paredes, pé-direito, tipo de telhado pelas bordas com caimento, contorno
e beiral pelas faces das paredes, rincão/encostado/parede alta/platibanda automáticos, direção das vigas do
piso, escadas, caixas d'água e ligação de cada erro ao elemento do Revit.
"""
from __future__ import annotations

import math
import re

from .model import Project

# chave WALL_KEY_REF_PARAM do Revit -> deslocamento do eixo em relação à curva (em frações da espessura,
# no sentido da orientação da parede, que aponta para o lado externo)
HEAL_GAP = 5.0       # folga máxima de desenho corrigida automaticamente (mm); acima disso é erro V-075
MIN_WALL_WIDTH = 38.0

LOCATION_LINE = {0: 0.0, 1: 0.0, 2: -0.5, 3: 0.5, 4: -0.5, 5: 0.5}

HINTS = {
    "V-075": "Ajuste a parede para encostar na outra (una as paredes no Revit) ou afaste pelo menos 300 mm.",
    "V-078": "Desenhe o encontro a 90° ou entre 120° e 180° (use o snap de ângulo).",
    "V-069": "Afaste a porta/janela do encontro em T (a parede que chega não pode cair sobre a abertura).",
    "V-018": "Afaste a abertura pelo menos 100 mm do canto.",
    "V-019": "Aberturas muito próximas: afaste ou una as duas em uma só.",
    "V-080": "O telhado precisa de paredes portantes (estruturais) nas bordas com caimento.",
    "V-076": "As paredes de apoio do telhado/entrepiso precisam ter a mesma altura.",
    "V-086": "Aumente a altura da parede alta/platibanda para cobrir o telhado.",
    "V-088": "A cumeeira da asa precisa ficar abaixo da cumeeira do telhado principal.",
    "V-090": "Mova a caixa para perto da cumeeira ou aumente a inclinação do telhado.",
    "V-091": "Coloque a caixa entre duas paredes estruturais paralelas a até 1,50 m (hall, banheiro, shaft).",
    "V-083": "Aumente o furo do piso no sentido da subida da escada.",
    "V-085": "A escada bate em uma parede: mova a escada ou a parede.",
    "V-095": "Desenhe um telhado por volume, retangular e alinhado aos eixos do projeto.",
    "V-096": "Escada em lance reto alinhada aos eixos; escadas em L/U ainda não são suportadas.",
    "V-121": "Correção automática pequena (até 5 mm). Para eliminar, una as paredes no Revit.",
    "V-128": "Apague a parede duplicada no Revit.",
    "V-130": "Parede de comprimento zero: apague no Revit.",
    "V-131": "Parede sem espessura (separação de ambientes) não gera framing.",
}


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _issue(out, code, sev, element, msg, rids=()):
    out.append({"code": code, "severity": sev, "element": element, "message": msg, "rids": list(rids),
                "hint": HINTS.get(code, "")})


def normalize(raw: dict, cfg: dict | None = None) -> tuple[Project, list]:
    """Retorna (projeto, avisos_da_importação)."""
    cfg = cfg or {}
    notes: list = []
    system = cfg.get("system", "wood")
    ruleset = cfg.get("ruleset") or ("wood-br-v1" if system == "wood" else "steel-br-v1")
    wall_types = cfg.get("wall_types", {})             # nome do tipo Revit -> {"exterior", "bearing", "wall_type"}
    wall_over = {int(k): v for k, v in cfg.get("walls", {}).items()}
    roof_over = {int(k): v for k, v in cfg.get("roofs", {}).items()}
    floor_over = {int(k): v for k, v in cfg.get("floors", {}).items()}

    # ---------------- níveis: pé-direito = diferença até o nível de cima
    lv_raw = sorted(raw.get("levels", []), key=lambda l: l["elevation"])
    lv_id = {}
    levels = []
    for i, l in enumerate(lv_raw):
        lid = "L%d" % (i + 1)
        lv_id[l["rid"]] = lid
        nxt = lv_raw[i + 1]["elevation"] - l["elevation"] if i + 1 < len(lv_raw) else None
        levels.append({"id": lid, "name": l["name"], "elevation": round(l["elevation"], 1),
                       "height": round(nxt, 1) if nxt and nxt > 1500 else 2700.0})

    # ---------------- paredes
    walls, curved = [], []
    seen_geo = {}
    for w in raw.get("walls", []):
        if w["level_rid"] not in lv_id:
            continue
        if w.get("width", 140.0) < MIN_WALL_WIDTH:
            _issue(notes, "V-131", "info", "W%d" % w["rid"], "parede sem espessura estrutural ignorada", [w["rid"]])
            continue
        c_ = w["curve"]
        if c_["kind"] == "line":
            if _dist(c_["p0"], c_["p1"]) < 1.0:
                _issue(notes, "V-130", "info", "W%d" % w["rid"], "parede de comprimento zero ignorada", [w["rid"]])
                continue
            key = (w["level_rid"],) + tuple(sorted([tuple(round(v / 5) for v in c_["p0"]), tuple(round(v / 5) for v in c_["p1"])]))
            if key in seen_geo:
                _issue(notes, "V-128", "warning", "W%d" % w["rid"],
                       "parede duplicada de W%d (mesma posição) ignorada" % seen_geo[key], [w["rid"], seen_geo[key]])
                continue
            seen_geo[key] = w["rid"]
        wt = wall_types.get(w.get("type_name", ""), {})
        ov = wall_over.get(w["rid"], {})
        ext = ov.get("exterior", wt.get("exterior", w.get("type_function") == "Exterior"))
        bear = ov.get("bearing", wt.get("bearing", bool(w.get("structural", ext))))
        wid = "W%d" % w["rid"]
        c = w["curve"]
        k = LOCATION_LINE.get(int(w.get("location_line", 0)), 0.0)
        o = w.get("orientation", [0.0, 0.0])
        sh = (o[0] * k * w.get("width", 0.0), o[1] * k * w.get("width", 0.0))
        if c["kind"] == "arc":
            curved.append({"id": wid, "level": lv_id[w["level_rid"]], "center": c["center"], "radius": c["radius"],
                           "angle_start": c["a0"], "angle_end": c["a1"], "height": w["height"], "exterior": ext,
                           "bearing": bear})
            continue
        p0 = (c["p0"][0] + sh[0], c["p0"][1] + sh[1])
        p1 = (c["p1"][0] + sh[0], c["p1"][1] + sh[1])
        ops = []
        for ins in w.get("inserts", []):
            ops.append({"id": "O%d" % ins["rid"], "kind": "door" if ins["category"] == "door" else "window",
                        "offset": round(ins["center_along"] - ins["width"] / 2, 1), "width": round(ins["width"], 1),
                        "height": round(ins["height"], 1), "sill": round(ins.get("sill", 0.0), 1)})
        item = {"id": wid, "level": lv_id[w["level_rid"]], "start": [round(p0[0], 1), round(p0[1], 1)],
                "end": [round(p1[0], 1), round(p1[1], 1)], "height": round(w["height"], 1), "exterior": ext,
                "bearing": bear, "openings": ops}
        if ov.get("wall_type") or wt.get("wall_type"):
            item["wall_type"] = ov.get("wall_type") or wt.get("wall_type")
        walls.append(item)

    heal_walls(walls, {("W%d" % w["rid"]): w.get("width", 140.0) for w in raw.get("walls", [])}, notes,
               centered={("W%d" % w["rid"]) for w in raw.get("walls", []) if int(w.get("location_line", 0)) in (0, 1)})

    def faces(level_id, axis):
        """Faces externas das paredes externas: (coordenada, extensão) para 'x' (paredes ao longo de x)."""
        out = []
        for w in walls:
            if w["level"] != level_id or not w["exterior"]:
                continue
            (x0, y0), (x1, y1) = w["start"], w["end"]
            along_x = abs(y1 - y0) < 1.0
            along_y = abs(x1 - x0) < 1.0
            if (axis == "x" and along_x) or (axis == "y" and along_y):
                c_ = y0 if axis == "x" else x0
                e0, e1 = sorted((x0, x1) if axis == "x" else (y0, y1))
                out.append((c_, e0, e1))
        return out

    # espessura do quadro da parede externa (das regras) para achar as faces externas
    from .config import Catalog, Rules
    try:
        _rules, _cat = Rules.load(ruleset), Catalog.load()
        _wt = cfg.get("exterior_wall_type", "PE-01")
        wall_depth = float(_cat.depth(_rules.data["wall_types"][_wt]["stud"]))
    except Exception:                                        # regras ausentes: padrão wood
        wall_depth = 140.0

    # ---------------- telhados (telhado por perímetro): tipo pelas bordas com caimento
    roofs = []
    for r in raw.get("roofs", []):
        rid = "R%d" % r["rid"]
        if r["level_rid"] not in lv_id:
            continue
        lvl = lv_id[r["level_rid"]]
        edges = _merge_edges(r.get("edges", []))
        axis_ok = all(abs(e["p0"][0] - e["p1"][0]) < 1 or abs(e["p0"][1] - e["p1"][1]) < 1 for e in edges)
        xs = [p[0] for e in edges for p in (e["p0"], e["p1"])]
        ys = [p[1] for e in edges for p in (e["p0"], e["p1"])]
        if not edges or not axis_ok or len(edges) != 4:
            _issue(notes, "V-095", "error", rid, "telhado não retangular ou girado: um telhado por volume, "
                                                 "retangular e alinhado aos eixos", [r["rid"]])
            continue
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        sides = {}
        for e in edges:
            if abs(e["p0"][1] - e["p1"][1]) < 1:                      # borda ao longo de x
                sides["S" if abs(e["p0"][1] - by0) < 1 else "N"] = e
            else:
                sides["W" if abs(e["p0"][0] - bx0) < 1 else "E"] = e
        sl = {k for k, e in sides.items() if e.get("slope")}
        pitch = [e["angle_deg"] for e in sides.values() if e.get("slope")]
        ov = roof_over.get(r["rid"], {})
        spec = {"id": rid, "level": lvl, "pitch_deg": round(sum(pitch) / len(pitch), 2) if pitch else 0.0}
        if sl == {"S", "N", "W", "E"}:
            spec["kind"] = "hip"
            spec["ridge_axis"] = "x" if (bx1 - bx0) >= (by1 - by0) else "y"
        elif sl in ({"S", "N"}, {"W", "E"}):
            spec["kind"] = "gable"
            spec["ridge_axis"] = "x" if sl == {"S", "N"} else "y"
        elif len(sl) == 1:
            s_ = next(iter(sl))
            spec["kind"] = "mono"
            spec["ridge_axis"] = "x" if s_ in ("S", "N") else "y"
            spec["high_side"] = "end" if s_ in ("S", "W") else "start"     # borda com caimento = lado baixo
        else:
            _issue(notes, "V-095", "error", rid, "telhado plano ou com caimentos não suportados: defina caimento "
                                                 "em 1 (meia-água), 2 opostas (2 águas) ou 4 bordas (4 águas)", [r["rid"]])
            continue
        # contorno pelas faces externas das paredes (o desenho do Revit pode incluir o beiral)
        fx = faces(lvl, "x")
        fy = faces(lvl, "y")

        hd = wall_depth / 2

        def side(val, axis_list, outward):
            """(coordenada do contorno, encosta?) para uma borda do desenho.
            outward = +1 se o lado externo da borda fica no sentido positivo do eixo (N/E), -1 (S/W)."""
            best = None
            for c_, e0, e1 in axis_list:
                face_out = c_ + outward * hd                 # face externa de uma parede neste lado
                d = (val - face_out) * outward               # >= 0: desenho passa da face (beiral)
                if -5 <= d <= 1200 and (best is None or d < best[1]):
                    best = (face_out, d)
            if best is not None:
                return best[0], False
            for c_, e0, e1 in axis_list:                     # borda sobre a face de parede com eixo fora do telhado
                if abs((c_ - outward * hd) - val) < 5 and (c_ - val) * outward > 0:
                    return val, True
            return val, False

        oy0, t_s = side(by0, fx, -1)
        oy1, t_n = side(by1, fx, 1)
        ox0, t_w = side(bx0, fy, -1)
        ox1, t_e = side(bx1, fy, 1)
        inside = t_s and t_n and t_w and t_e
        if inside:                                           # platibanda: contorno nas faces externas
            oy0, oy1, ox0, ox1 = by0 - wall_depth, by1 + wall_depth, bx0 - wall_depth, bx1 + wall_depth
        if inside:                                # telhado desenhado por dentro das paredes = platibanda
            spec["support"] = "parapet"
            spec["bearing_height"] = round(r.get("base_offset", 0.0) or 2700.0, 1)
        else:
            eave = [oy0 - by0, by1 - oy1] if spec["ridge_axis"] == "x" else [ox0 - bx0, bx1 - ox1]
            ovh = max([v for v in eave if v > 5] or [0.0])
            if ovh > 0:
                spec["overhang"] = round(ovh, 1)
        spec["outline"] = [[ox0, oy0], [ox1, oy0], [ox1, oy1], [ox0, oy1]]
        for k_, v in ov.items():                  # escolhas do usuário vencem a detecção
            if v not in (None, "", "auto"):
                spec[k_] = v
        roofs.append(spec)

    # parede alta automática (meia-água cujo lado alto tem paredes mais altas)
    for spec in roofs:
        if spec["kind"] != "mono" or spec.get("support") not in (None, "walls"):
            continue
        (ox0, oy0), (ox1, _), (_, oy1) = spec["outline"][0], spec["outline"][1], spec["outline"][2]
        hi_c = (oy1 if spec["high_side"] == "end" else oy0) if spec["ridge_axis"] == "x" else \
            (ox1 if spec["high_side"] == "end" else ox0)
        lo_c = (oy0 if spec["high_side"] == "end" else oy1) if spec["ridge_axis"] == "x" else \
            (ox0 if spec["high_side"] == "end" else ox1)
        hs = [w["height"] for w in walls if w["level"] == spec["level"] and _wall_on(w, spec["ridge_axis"], hi_c, wall_depth)]
        ls = [w["height"] for w in walls if w["level"] == spec["level"] and _wall_on(w, spec["ridge_axis"], lo_c, wall_depth)]
        if hs and ls and min(hs) > max(ls) + 300:
            spec["support"] = "high_wall"

    # rincão / encostado automáticos entre telhados de 2 águas
    for a in roofs:
        if a["kind"] != "gable" or "ends" in a:
            continue
        ax0, ay0 = a["outline"][0]
        ax1, ay1 = a["outline"][2]
        ends = ["gable", "gable"]
        a_al = (ax0, ax1) if a["ridge_axis"] == "x" else (ay0, ay1)
        a_sp = (ay0, ay1) if a["ridge_axis"] == "x" else (ax0, ax1)
        for i, fc in enumerate(a_al):
            for b in roofs:
                if b is a or b["level"] != a["level"]:
                    continue
                bx0, by0 = b["outline"][0]
                bx1, by1 = b["outline"][2]
                b_al = (bx0, bx1) if a["ridge_axis"] == "x" else (by0, by1)     # no eixo da cumeeira de 'a'
                b_sp = (by0, by1) if a["ridge_axis"] == "x" else (bx0, bx1)
                beyond = b_al[1] <= fc + 5 if i == 0 else b_al[0] >= fc - 5  # 'b' fica além desta ponta
                touches = abs((b_al[1] if i == 0 else b_al[0]) - fc) < 5
                overlap = min(a_sp[1], b_sp[1]) - max(a_sp[0], b_sp[0]) > 100
                if not (beyond and touches and overlap):
                    continue
                if b["ridge_axis"] != a["ridge_axis"] and b["kind"] in ("gable", "hip"):
                    ends[i] = "valley"                       # a asa encosta no beiral do principal
                elif _ridge_rise(a) <= _ridge_rise(b):       # ponta a ponta: só o volume mais baixo encosta
                    ends[i] = "abut"
        if ends != ["gable", "gable"]:
            a["ends"] = ends

    # ---------------- pisos (entrepisos)
    floors = []
    for f in raw.get("floors", []):
        if f["level_rid"] not in lv_id or lv_id[f["level_rid"]] == levels[0]["id"]:
            continue                                    # piso do térreo é fundação/radier (fora do framing)
        loops = sorted(f["loops"], key=lambda lp: -abs(_area(lp)))
        fid = "F%d" % f["rid"]
        lvl = lv_id[f["level_rid"]]
        ov = floor_over.get(f["rid"], {})
        jd = ov.get("joist_direction") or _auto_joists(walls, lvl, levels, loops[0])
        floors.append({"id": fid, "level": lvl, "outline": [[round(p[0], 1), round(p[1], 1)] for p in loops[0]],
                       "holes": [[[round(p[0], 1), round(p[1], 1)] for p in lp] for lp in loops[1:]],
                       "joist_direction": jd})

    # ---------------- escadas (lance reto)
    stairs = []
    for s in raw.get("stairs", []):
        runs = s.get("runs", [])
        sid = "S%d" % s["rid"]
        if len(runs) != 1 or s.get("top_level_rid") not in lv_id:
            _issue(notes, "V-096", "warning", sid, "escada ignorada: só lance reto único entre dois níveis",
                   [s["rid"]])
            continue
        r0 = runs[0]
        d = (r0["end"][0] - r0["start"][0], r0["end"][1] - r0["start"][1])
        L = math.hypot(*d) or 1.0
        u = (d[0] / L, d[1] / L)
        if abs(abs(u[0]) - 1) < 0.01:
            dirs = "+x" if u[0] > 0 else "-x"
        elif abs(abs(u[1]) - 1) < 0.01:
            dirs = "+y" if u[1] > 0 else "-y"
        else:
            _issue(notes, "V-096", "warning", sid, "escada girada em relação aos eixos: ignorada", [s["rid"]])
            continue
        stairs.append({"id": sid, "level": lv_id[s["top_level_rid"]], "start": [round(r0["start"][0], 1),
                                                                               round(r0["start"][1], 1)],
                       "direction": dirs, "width": round(r0["width"], 1)})

    # ---------------- caixas d'água (família no Revit ou configuração)
    tanks = []
    for t in raw.get("tanks", []):
        if t["level_rid"] not in lv_id:
            continue
        tk = {"id": "CX%d" % t["rid"], "model": t.get("model") or "BR_1000L", "level": lv_id[t["level_rid"]]}
        if not t.get("auto"):
            tk["position"] = [round(t["point"][0], 1), round(t["point"][1], 1)]
        tanks.append(tk)
    for t in cfg.get("tanks", []):                      # caixa criada pelo botão do plugin (sem família)
        tk = {"id": t.get("id", "CX1"), "model": t.get("model", "BR_1000L"),
              "level": lv_id.get(t.get("level_rid"), t.get("level", levels[0]["id"] if levels else "L1"))}
        if t.get("position"):
            tk["position"] = [round(t["position"][0], 1), round(t["position"][1], 1)]
        tanks.append(tk)

    meta = dict(cfg.get("meta", {}))
    proj = Project.model_validate({
        "id": cfg.get("project_id", "RVT"), "name": raw.get("doc", {}).get("title", "Modelo Revit"),
        "system": system, "ruleset": ruleset, "levels": levels, "walls": walls, "curved_walls": curved,
        "roofs": roofs, "floors": floors, "stairs": stairs, "tanks": tanks, "meta": meta})
    for r in proj.roofs:
        spc = dict(cfg.get("roof_defaults", {}))
        pref = spc.pop("truss_type", None)
        if pref and not r.truss_type:
            r.truss_type_pref = pref                          # padrão do projeto: só onde o vão couber
        for k_, v in spc.items():
            if v not in (None, "", "auto") and getattr(r, k_, None) in (None, "") and k_ != "outline":
                setattr(r, k_, v)
    return proj, notes


def _line_inter(p0, p1, q0, q1):
    """Interseção das retas infinitas p0-p1 e q0-q1 (None se paralelas)."""
    d1 = (p1[0] - p0[0], p1[1] - p0[1])
    d2 = (q1[0] - q0[0], q1[1] - q0[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    L = math.hypot(*d1) * math.hypot(*d2)
    if L == 0 or abs(den) < 1e-6 * L:
        return None
    t = ((q0[0] - p0[0]) * d2[1] - (q0[1] - p0[1]) * d2[0]) / den
    return (p0[0] + d1[0] * t, p0[1] + d1[1] * t)


def heal_walls(walls, widths, notes=None, extra=60.0, centered=()):  # noqa: C901
    """Costura as pontas no eixo depois da correção da linha de localização do Revit.

    Canto L: as duas pontas vão para o cruzamento dos eixos. Encontro T: a ponta vai para o eixo da parede
    que ela encontra (vale se o Revit parou a curva na face ou na linha de localização da outra). Ponta que
    passa um pouco da outra parede é aparada. Só mexe quando a distância é menor que as meias espessuras + 60 mm.
    """
    for _ in range(3):
        moved = 0
        for a in walls:
            for end in ("start", "end"):
                P = tuple(a[end])
                Q = tuple(a["end"] if end == "start" else a["start"])
                La = _dist(P, Q)
                if La < 1:
                    continue
                best = None
                for b in walls:
                    if b is a or b["level"] != a["level"]:
                        continue
                    B0, B1 = tuple(b["start"]), tuple(b["end"])
                    Lb = _dist(B0, B1)
                    if Lb < 1:
                        continue
                    tol = (widths.get(a["id"], 140.0) + widths.get(b["id"], 140.0)) / 2 + extra
                    X = _line_inter(P, Q, B0, B1)
                    if X is None:                       # paralelas: continuação na mesma linha
                        for Bx in (B0, B1):
                            ub = ((B1[0] - B0[0]) / Lb, (B1[1] - B0[1]) / Lb)
                            off = abs((P[0] - B0[0]) * ub[1] - (P[1] - B0[1]) * ub[0])
                            d = _dist(P, Bx)
                            if off < 5 and 0.5 < d < tol and (best is None or d < best[0]):
                                best = (d, ((P[0] + Bx[0]) / 2, (P[1] + Bx[1]) / 2), b, Bx)
                        continue
                    d = _dist(P, X)
                    if d < 0.5 or d > tol:
                        continue
                    ub = ((B1[0] - B0[0]) / Lb, (B1[1] - B0[1]) / Lb)
                    tb = (X[0] - B0[0]) * ub[0] + (X[1] - B0[1]) * ub[1]
                    if tb < -tol or tb > Lb + tol:      # o cruzamento precisa estar na parede b (ou na ponta dela)
                        continue
                    ua = ((Q[0] - P[0]) / La, (Q[1] - P[1]) / La)
                    ta = (X[0] - P[0]) * ua[0] + (X[1] - P[1]) * ua[1]
                    if ta > La - 1:                     # não pode atravessar a própria parede
                        continue
                    if best is None or d < best[0]:
                        bend = B0 if abs(tb) <= tol and abs(tb) < abs(Lb - tb) else (B1 if abs(Lb - tb) <= tol else None)
                        best = (d, X, b, bend)
            # aplica (e leva junto a ponta da outra parede no canto L)
                if best is None:
                    continue
                d, X, b, bend = best
                X = (round(X[0], 1), round(X[1], 1))
                wa_, wb_ = widths.get(a["id"], 140.0), widths.get(b["id"], 140.0)
                # padrões legítimos do Revit: ponta no eixo, na face de uma das paredes, ou nas duas faces
                padroes = (0.0, wa_ / 2, wb_ / 2, (wa_ + wb_) / 2)
                excess = min(abs(d - k) for k in padroes)
                if excess > HEAL_GAP + 0.5:                   # folga real de desenho > 5 mm: não corrige (V-075)
                    continue
                if notes is not None and excess > 0.5:        # correção pequena, sempre registrada
                    _issue(notes, "V-121", "info", a["id"],
                           "ponta da parede ajustada %.1f mm para encontrar %s (folga no desenho do Revit)" % (excess, b["id"]),
                           [int(a["id"][1:].rstrip("AB"))])
                _move_end(a, end, X)
                if bend is not None:
                    bkey = "start" if tuple(b["start"]) == tuple(bend) else "end"
                    if _dist(tuple(b[bkey]), X) <= (widths.get(a["id"], 140.0) + widths.get(b["id"], 140.0)) / 2 + extra:
                        _move_end(b, bkey, X)
                moved += 1
        if not moved:
            break


def _move_end(w, end, X):
    """Move a ponta e mantém as aberturas no mesmo lugar (offset medido a partir do início)."""
    old = tuple(w[end])
    if end == "start":
        e = tuple(w["end"])
        L = _dist(old, e)
        if L > 0:
            u = ((e[0] - old[0]) / L, (e[1] - old[1]) / L)
            shift = (X[0] - old[0]) * u[0] + (X[1] - old[1]) * u[1]
            for o in w["openings"]:
                o["offset"] = round(o["offset"] - shift, 1)
    w[end] = [X[0], X[1]]


def _merge_edges(edges):
    """Junta segmentos colineares e contíguos com o mesmo caimento (bordas divididas no esboço do Revit)."""
    es = [dict(e) for e in edges]
    changed = True
    while changed and len(es) > 1:
        changed = False
        for i in range(len(es)):
            a, b = es[i], es[(i + 1) % len(es)]
            if a is b or bool(a.get("slope")) != bool(b.get("slope")):
                continue
            d1 = (a["p1"][0] - a["p0"][0], a["p1"][1] - a["p0"][1])
            d2 = (b["p1"][0] - b["p0"][0], b["p1"][1] - b["p0"][1])
            cross = d1[0] * d2[1] - d1[1] * d2[0]
            if _dist(a["p1"], b["p0"]) < 1 and abs(cross) < 1e-3 * (math.hypot(*d1) * math.hypot(*d2) + 1):
                a["p1"] = b["p1"]
                es.pop((i + 1) % len(es))
                changed = True
                break
    return es


def _ridge_rise(r):
    x0, y0 = r["outline"][0]
    x1, y1 = r["outline"][2]
    span = (y1 - y0) if r["ridge_axis"] == "x" else (x1 - x0)
    return (span if r["kind"] == "mono" else span / 2) * math.tan(math.radians(r["pitch_deg"]))


def _wall_on(w, axis, coord, depth=140.0, tol=100.0):
    (x0, y0), (x1, y1) = w["start"], w["end"]
    if axis == "x":
        return abs(y1 - y0) < 1 and abs(abs(y0 - coord) - depth / 2) < tol
    return abs(x1 - x0) < 1 and abs(abs(x0 - coord) - depth / 2) < tol


def _area(loop):
    return sum(loop[i][0] * loop[(i + 1) % len(loop)][1] - loop[(i + 1) % len(loop)][0] * loop[i][1]
               for i in range(len(loop))) / 2.0


def _auto_joists(walls, level_id, levels, outline):
    """Direção das vigas: a que dá o menor vão máximo entre paredes portantes do pavimento de baixo."""
    ids = [l["id"] for l in levels]
    below = ids[ids.index(level_id) - 1] if level_id in ids and ids.index(level_id) > 0 else None
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    best = None
    for jd in ("x", "y"):
        sup = []
        for w in walls:
            if w["level"] != below or not w["bearing"]:
                continue
            (x0, y0), (x1, y1) = w["start"], w["end"]
            if jd == "y" and abs(y1 - y0) < 1 and min(x0, x1) <= cx <= max(x0, x1):
                sup.append(y0)                          # vigas em y apoiam em paredes ao longo de x
            if jd == "x" and abs(x1 - x0) < 1 and min(y0, y1) <= cy <= max(y0, y1):
                sup.append(x0)
        sup = sorted(set(sup))
        if len(sup) < 2:
            continue
        gap = max(b - a for a, b in zip(sup, sup[1:]))
        if best is None or gap < best[0]:
            best = (gap, jd)
    return best[1] if best else "y"


RID = re.compile(r"(?:^|[-_/+ ])(?:W|R|F|S|CX|O)(\d{3,})")


def issues_for_revit(result, notes=()) -> list:
    """Erros e avisos com os ids de elemento do Revit e uma dica de correção (para o botão Mostrar)."""
    out = list(notes)
    for i in result.issues:
        if i.severity == "info" and i.code == "V-000" and "caixa" not in i.message and "rincão" not in i.message:
            continue
        rids = sorted({int(m) for m in RID.findall(" " + (i.element or "")) + RID.findall(" " + i.message)})
        msg = i.message
        if i.element and i.element not in msg:
            msg = "[%s] %s" % (i.element.replace("RVT-", ""), msg)
        out.append({"code": i.code, "severity": i.severity, "element": i.element, "message": msg,
                    "rids": rids, "hint": HINTS.get(i.code, "")})
    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(out, key=lambda d: (order.get(d["severity"], 3), d["code"]))
