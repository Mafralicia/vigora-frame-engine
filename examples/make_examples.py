"""Gera os projetos de exemplo em JSON (entrada neutra do motor)."""
import json
from pathlib import Path

HERE = Path(__file__).parent


def w(id, level, a, b, h, ext=True, bearing=True, ops=(), **kw):
    return {"id": id, "level": level, "start": list(a), "end": list(b), "height": h, "exterior": ext,
            "bearing": bearing, "openings": list(ops), **kw}


def win(id, off, width, height, sill, **kw):
    return {"id": id, "kind": "window", "offset": off, "width": width, "height": height, "sill": sill, **kw}


def door(id, off, width, height=2100):
    return {"id": id, "kind": "door", "offset": off, "width": width, "height": height, "sill": 0}


def casa_terrea(system: str):
    """Casa térrea 8,40 x 7,20 m (60,5 m²), 2 águas, 3 ambientes."""
    H = 2700
    L = "L1"
    walls = [
        w("W01", L, (70, 70), (8330, 70), H, ops=[win("J1", 900, 1500, 1200, 1000), door("P1", 5000, 1000),
                                                  win("J2", 6800, 1000, 1200, 1000)]),
        w("W02", L, (8330, 70), (8330, 7130), H, ops=[door("P2", 3000, 900)]),
        w("W03", L, (70, 7130), (8330, 7130), H, ops=[win("J3", 1200, 1200, 1200, 1000), win("J4", 5400, 600, 600, 1500)]),
        w("W04", L, (70, 70), (70, 7130), H, ops=[win("J5", 1600, 1200, 1200, 1000)]),
        w("W05", L, (4200, 70), (4200, 7130), H, ext=False, bearing=False, ops=[door("P3", 1500, 800), door("P4", 4500, 800)]),
        w("W06", L, (70, 3600), (4200, 3600), H, ext=False, bearing=False, ops=[door("P5", 2000, 800)]),
    ]
    return {"id": "CT01" if system == "wood" else "CT02",
            "name": f"Casa térrea 60 m² ({'wood frame' if system == 'wood' else 'steel frame'})",
            "system": system, "ruleset": "wood-br-v1" if system == "wood" else "steel-br-v1",
            "levels": [{"id": L, "name": "Térreo", "elevation": 0, "height": H}],
            "walls": walls,
            "roofs": [{"id": "R1", "level": L, "kind": "gable", "ridge_axis": "x", "pitch_deg": 25}]}


def sobrado():
    """Sobrado 9,60 x 6,00 m (2 x 57,6 m²), entrepiso com escada, parede portante central."""
    H = 2700
    walls = [
        w("S1", "L1", (70, 70), (9530, 70), H, ops=[win("J1", 800, 1500, 1200, 1000), door("P1", 4200, 1000),
                                                    win("J2", 7200, 1500, 1200, 1000)]),
        w("N1", "L1", (70, 5930), (9530, 5930), H, ops=[win("J3", 2500, 1200, 1200, 1000), win("J4", 6800, 1200, 1200, 1000)]),
        w("W1", "L1", (70, 70), (70, 5930), H, ops=[]),
        w("E1", "L1", (9530, 70), (9530, 5930), H, ops=[door("P2", 1200, 900)]),
        w("B1", "L1", (70, 3000), (9530, 3000), H, ext=False, bearing=True, ops=[door("P3", 800, 900), door("P4", 7200, 900)]),
        w("X1", "L1", (3400, 70), (3400, 3000), H, ext=False, bearing=False, ops=[door("P5", 1200, 800)]),
        w("S2", "L2", (70, 70), (9530, 70), 2600, ops=[win("J5", 1200, 1200, 1100, 1000), win("J6", 5200, 1200, 1100, 1000),
                                                       win("J7", 7800, 800, 600, 1500)]),
        w("N2", "L2", (70, 5930), (9530, 5930), 2600, ops=[win("J8", 700, 1500, 1100, 1000), win("J9", 7200, 1500, 1100, 1000)]),
        w("W2", "L2", (70, 70), (70, 5930), 2600, ops=[win("J10", 3000, 1000, 1100, 1000)]),
        w("E2", "L2", (9530, 70), (9530, 5930), 2600, ops=[]),
        w("X2", "L2", (2950, 70), (2950, 5930), 2600, ext=False, bearing=False, ops=[door("P6", 3600, 800)]),
        w("X3", "L2", (6800, 70), (6800, 5930), 2600, ext=False, bearing=False, ops=[door("P7", 3600, 800)]),
    ]
    return {"id": "SB01", "name": "Sobrado 115 m² (wood frame)", "system": "wood", "ruleset": "wood-br-v1",
            "levels": [{"id": "L1", "name": "Térreo", "elevation": 0, "height": 2700},
                       {"id": "L2", "name": "Superior", "elevation": 2953, "height": 2600}],
            "walls": walls,
            "floors": [{"id": "F2", "level": "L2", "outline": [[0, 0], [9600, 0], [9600, 6000], [0, 6000]],
                        "holes": [[[3030, 3080], [6700, 3080], [6700, 4080], [3030, 4080]]], "joist_direction": "y"}],
            "roofs": [{"id": "R1", "level": "L2", "kind": "gable", "ridge_axis": "x", "pitch_deg": 30}],
            "stairs": [{"id": "E1", "level": "L2", "start": [2200, 3580], "direction": "+x", "width": 960}]}


def pavilhao():
    """Pavilhão com parede curva (R=3 m), janela em arco e pilar isolado."""
    H = 2700
    walls = [
        w("S1", "L1", (70, 70), (6070, 70), H, ops=[win("A1", 1500, 1200, 1800, 600, kind="arch", rise=600)]),
        w("W1", "L1", (70, 70), (70, 4070), H, ops=[door("P1", 1500, 900)]),
        w("N1", "L1", (70, 4070), (3070, 4070), H, ops=[]),
        w("E1", "L1", (6070, 1070), (6070, 70), H, ops=[]),
    ]
    return {"id": "PV01", "name": "Pavilhão com parede curva e arco (wood frame)", "system": "wood",
            "ruleset": "wood-br-v1",
            "levels": [{"id": "L1", "name": "Térreo", "elevation": 0, "height": H}],
            "walls": walls,
            "curved_walls": [{"id": "C1", "level": "L1", "center": [3070, 1070], "radius": 3000,
                              "angle_start": 90, "angle_end": 0, "height": H, "exterior": True, "bearing": False}],
            "columns": [{"id": "PL1", "level": "L1", "position": [4500, 2500], "height": 2700,
                         "tributary_area_m2": 6.0}]}


if __name__ == "__main__":
    for name, data in (("casa_terrea_wood", casa_terrea("wood")), ("casa_terrea_steel", casa_terrea("steel")),
                       ("sobrado_wood", sobrado()), ("pavilhao_curvo", pavilhao())):
        (HERE / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        print("ok", name)


# ============================================================ novos projetos (variedade)
def rect(prefix, level, x0, y0, x1, y1, H, ops=None, d=140, ext=True, bearing=True, sides=None):
    """Quatro paredes externas pelo eixo (a face externa fica em x0..x1, y0..y1).

    ops: dict lado -> aberturas; lados S (sul, y0), N (norte, y1), W (oeste, x0), E (leste, x1).
    O eixo fica recuado d/2 da face externa; 'offset' de cada abertura é medido do início do eixo.
    """
    h = d / 2
    ops = ops or {}
    pts = {"S": ((x0 + h, y0 + h), (x1 - h, y0 + h)), "N": ((x0 + h, y1 - h), (x1 - h, y1 - h)),
           "W": ((x0 + h, y0 + h), (x0 + h, y1 - h)), "E": ((x1 - h, y0 + h), (x1 - h, y1 - h))}
    out = []
    for side in (sides or "SNWE"):
        a, b = pts[side]
        out.append(w(f"{prefix}{side}", level, a, b, H, ext=ext, bearing=bearing, ops=ops.get(side, [])))
    return out


def iw(id, level, a, b, H, bearing=False, ops=()):
    return w(id, level, a, b, H, ext=False, bearing=bearing, ops=ops)


def proj(id, name, system, levels, walls, roofs=(), floors=(), curved=(), columns=(), stairs=()):
    return {"id": id, "name": name, "system": system, "ruleset": "wood-br-v1" if system == "wood" else "steel-br-v1",
            "levels": levels, "walls": walls, "roofs": list(roofs), "floors": list(floors),
            "curved_walls": list(curved), "columns": list(columns), "stairs": list(stairs)}


L1 = [{"id": "L1", "name": "Térreo", "elevation": 0, "height": 2700}]


def casa_4aguas(system="wood", pid="CT03"):
    """Casa 72 m² (9,60 x 7,50) com telhado 4 águas, cruzamento em X e vários T."""
    H = 2700
    walls = rect("E", "L1", 0, 0, 9600, 7500, H, ops={
        "S": [win("J1", 700, 1500, 1200, 1000), door("P1", 4300, 1000), win("J2", 7000, 1500, 1200, 1000)],
        "N": [win("J3", 900, 1200, 1200, 1000), win("J4", 4600, 600, 600, 1500), win("J5", 7200, 1200, 1200, 1000)],
        "W": [win("J6", 1000, 1500, 1200, 1000)],
        "E": [door("P2", 1200, 900)]})
    walls += [
        iw("I1", "L1", (3600, 70), (3600, 7430), H, ops=[door("P3", 900, 800), door("P4", 5000, 800)]),
        iw("I2", "L1", (70, 3900), (9530, 3900), H, bearing=True, ops=[door("P5", 1400, 800), door("P6", 5000, 900)]),
        iw("I3", "L1", (6600, 3900), (6600, 7430), H, ops=[door("P7", 700, 800)]),
    ]
    return proj(pid, f"Casa 72 m² 4 águas ({system})", system, L1, walls,
                roofs=[{"id": "R1", "level": "L1", "kind": "hip", "ridge_axis": "x", "pitch_deg": 22}])


def casa_meia_agua(system="wood", pid="CT04", high="end"):
    """Casa contemporânea 55 m² (8,40 x 6,60), meia-água, janelões."""
    H = 2700
    walls = rect("E", "L1", 0, 0, 8400, 6600, H, ops={
        "S": [win("J1", 500, 2000, 1500, 700), door("P1", 3200, 900), win("J2", 5600, 2000, 1500, 700)],
        "N": [win("J3", 1000, 1200, 1000, 1100), win("J4", 5200, 800, 600, 1500)],
        "W": [win("J5", 2000, 1500, 1200, 1000)],
        "E": []})
    walls += [iw("I1", "L1", (4800, 70), (4800, 6530), H, ops=[door("P2", 4400, 800)]),
              iw("I2", "L1", (4800, 3300), (8330, 3300), H, ops=[door("P3", 1200, 800)])]
    return proj(pid, f"Casa 55 m² meia-água ({system})", system, L1, walls,
                roofs=[{"id": "R1", "level": "L1", "kind": "mono", "ridge_axis": "x", "pitch_deg": 10,
                        "high_side": high}])


def casa_em_L():
    """Casa em L: bloco principal 2 águas 25° e anexo 2 águas 20° encostado no oitão (dois telhados)."""
    H = 2700
    walls = rect("M", "L1", 0, 0, 9000, 7200, H, ops={
        "S": [win("J1", 800, 1500, 1200, 1000), door("P1", 5000, 1000), win("J2", 6400, 1500, 1200, 1000)],
        "N": [win("J3", 1200, 1200, 1200, 1000), win("J4", 5800, 1200, 1200, 1000)],
        "W": [win("J5", 1200, 1500, 1200, 1000)],
        "E": [win("J6", 300, 600, 600, 1500), door("P2", 3200, 900)]})
    walls += [
        w("AS", "L1", (8930, 1270), (13730, 1270), H, ops=[win("J7", 1400, 1500, 1200, 1000)]),
        w("AN", "L1", (8930, 5930), (13730, 5930), H, ops=[win("J8", 1400, 1500, 1200, 1000)]),
        w("AE", "L1", (13730, 1270), (13730, 5930), H, ops=[door("P3", 1800, 900)]),
        iw("I1", "L1", (4500, 70), (4500, 7130), H, ops=[door("P4", 1500, 800), door("P5", 5000, 800)]),
        iw("I2", "L1", (70, 3600), (4500, 3600), H, ops=[door("P6", 2400, 800)]),
    ]
    return proj("CT05", "Casa em L com anexo (dois telhados)", "wood", L1, walls, roofs=[
        {"id": "R1", "level": "L1", "kind": "gable", "ridge_axis": "x", "pitch_deg": 25,
         "outline": [[0, 0], [9000, 0], [9000, 7200], [0, 7200]]},
        {"id": "R2", "level": "L1", "kind": "gable", "ridge_axis": "x", "pitch_deg": 20, "ends": ["abut", "gable"],
         "overhang": 626,
         "outline": [[9000, 1200], [13800, 1200], [13800, 6000], [9000, 6000]]}])


def chale():
    """Chalé 6,00 x 8,40 com telhado 2 águas a 40° e cumeeira em y."""
    H = 2700
    walls = rect("E", "L1", 0, 0, 6000, 8400, H, ops={
        "S": [door("P1", 2400, 1000), win("J1", 800, 800, 1200, 1000), win("J2", 4200, 800, 1200, 1000)],
        "N": [win("J3", 2200, 1500, 1500, 800)],
        "W": [win("J4", 1500, 1200, 1200, 1000), win("J5", 6200, 1200, 1200, 1000)],
        "E": [win("J6", 3200, 1500, 1200, 1000)]})
    walls += [iw("I1", "L1", (70, 5400), (5930, 5400), H, ops=[door("P2", 400, 800), door("P3", 4000, 800)]),
              iw("I2", "L1", (1800, 5400), (1800, 8330), H)]
    return proj("CT06", "Chalé 50 m² 2 águas 40°", "wood", L1, walls,
                roofs=[{"id": "R1", "level": "L1", "kind": "gable", "ridge_axis": "y", "pitch_deg": 40}])


def salao_festas():
    """Salão de festas 150 m² (15,00 x 10,00), 4 águas, portas de correr, bar com cantos a 135°, banheiros em X."""
    H = 3000
    walls = rect("E", "L1", 0, 0, 15000, 10000, H, ops={
        "S": [door("P1", 1200, 2400, 2400), door("P2", 6200, 2400, 2400), door("P3", 11200, 2400, 2400)],
        "N": [win("J1", 1500, 1500, 1000, 1200), win("J2", 4600, 1500, 1000, 1200), win("J3", 13000, 800, 600, 1800)],
        "W": [win("J4", 3000, 2000, 1200, 1100)],
        "E": [door("P4", 1500, 1000, 2100), win("J5", 5400, 1500, 1200, 1100)]})
    walls += [
        # banheiros: parede em x=12000 (norte) cruzada pela divisória y=7500 (X)
        iw("B1", "L1", (12000, 5500), (12000, 9930), H, ops=[door("P5", 400, 800)]),
        iw("B2", "L1", (10000, 7500), (14930, 7500), H, ops=[door("P6", 600, 800), door("P7", 3200, 800)]),
        iw("B3", "L1", (10000, 5500), (12000, 5500), H),
        iw("B4", "L1", (10000, 5500), (10000, 9930), H, ops=[door("P8", 700, 900)]),
        # balcão do bar com cantos a 135° (meia-esquadria)
        iw("K1", "L1", (3000, 6500), (6000, 6500), H, ops=[win("J6", 900, 1500, 1100, 1000)]),
        iw("K2", "L1", (6000, 6500), (7200, 7700), H),
        iw("K3", "L1", (7200, 7700), (7200, 9930), H, ops=[door("P9", 800, 800)]),
    ]
    return proj("SF01", "Salão de festas 150 m² 4 águas", "wood",
                [{"id": "L1", "name": "Térreo", "elevation": 0, "height": H}], walls,
                roofs=[{"id": "R1", "level": "L1", "kind": "hip", "ridge_axis": "x", "pitch_deg": 18,
                        "girder_setback": 2400}])


def sobrado_4aguas():
    """Sobrado 8,40 x 9,00 (2 x 75 m²), 4 águas, vigas em x com duas paredes portantes."""
    walls = rect("E", "L1", 0, 0, 8400, 9000, 2700, ops={
        "S": [win("J1", 600, 1500, 1200, 1000), door("P1", 3600, 1000), win("J2", 6000, 1200, 1200, 1000)],
        "N": [win("J3", 600, 1500, 1200, 1000), win("J4", 5800, 1200, 1200, 1000)],
        "W": [win("J5", 3200, 1500, 1200, 1000)],
        "E": [door("P2", 5000, 900)]})
    walls += [iw("I1", "L1", (2800, 70), (2800, 8930), 2700, bearing=True, ops=[door("P3", 1500, 900), door("P4", 6400, 900)]),
              iw("I2", "L1", (5600, 70), (5600, 8930), 2700, bearing=True, ops=[door("P5", 2000, 900), door("P6", 6000, 900)])]
    walls += rect("F", "L2", 0, 0, 8400, 9000, 2600, ops={
        "S": [win("J7", 800, 1200, 1100, 1000), win("J8", 3600, 1200, 1100, 1000), win("J9", 6700, 600, 600, 1500)],
        "N": [win("J10", 600, 1500, 1100, 1000), win("J11", 5800, 1200, 1100, 1000)],
        "W": [win("J12", 4000, 1200, 1100, 1000)],
        "E": [win("J13", 5400, 1200, 1100, 1000)]})
    walls += [iw("I3", "L2", (2800, 70), (2800, 8930), 2600, ops=[door("P7", 3000, 800)]),
              iw("I4", "L2", (5600, 70), (5600, 8930), 2600, ops=[door("P8", 3000, 800)]),
              iw("I5", "L2", (5600, 4500), (8330, 4500), 2600, ops=[door("P9", 800, 800)])]
    return proj("SB02", "Sobrado 150 m² 4 águas", "wood",
                [{"id": "L1", "name": "Térreo", "elevation": 0, "height": 2700},
                 {"id": "L2", "name": "Superior", "elevation": 2953.3, "height": 2600}], walls,
                floors=[{"id": "F2", "level": "L2", "outline": [[0, 0], [8400, 0], [8400, 9000], [0, 9000]],
                         "holes": [[[3000, 5150], [4000, 5150], [4000, 8800], [3000, 8800]]], "joist_direction": "x"}],
                roofs=[{"id": "R1", "level": "L2", "kind": "hip", "ridge_axis": "y", "pitch_deg": 25}],
                stairs=[{"id": "E1", "level": "L2", "start": [3500, 4320], "direction": "+y", "width": 960}])


NEW = {
    "casa_4aguas_wood": lambda: casa_4aguas("wood", "CT03"),
    "casa_4aguas_steel": lambda: casa_4aguas("steel", "CT09"),
    "casa_meia_agua_wood": lambda: casa_meia_agua("wood", "CT04"),
    "casa_meia_agua_steel_invertida": lambda: casa_meia_agua("steel", "CT10", high="start"),
    "casa_em_L_dois_telhados": casa_em_L,
    "chale_40graus": chale,
    "salao_de_festas": salao_festas,
    "sobrado_4aguas": sobrado_4aguas,
}

if __name__ == "__main__":
    for name, fn in NEW.items():
        (HERE / f"{name}.json").write_text(json.dumps(fn(), indent=1, ensure_ascii=False), encoding="utf-8")
        print("ok", name)


# ============================================================ fase 2: telhados
def casa_T():
    """Casa em T americana: principal 2 águas 25° + asa sul 2 águas 25° com rincão."""
    H = 2700
    walls = [
        w("N", "L1", (70, 7130), (10730, 7130), H, ops=[win("J1", 1200, 1500, 1200, 1000), win("J2", 7500, 1500, 1200, 1000)]),
        w("W", "L1", (70, 70), (70, 7130), H, ops=[win("J3", 2800, 1500, 1200, 1000)]),
        w("E", "L1", (10730, 70), (10730, 7130), H, ops=[door("P1", 2800, 900)]),
        w("S", "L1", (70, 70), (10730, 70), H, ops=[win("J4", 1200, 1500, 1200, 1000), door("P2", 4400, 1600),
                                                     win("J5", 8000, 1500, 1200, 1000)]),
        w("AW", "L1", (3670, -4130), (3670, 70), H, ops=[win("J6", 1500, 1200, 1200, 1000)]),
        w("AE", "L1", (7130, -4130), (7130, 70), H, ops=[win("J7", 1500, 1200, 1200, 1000)]),
        w("AS", "L1", (3670, -4130), (7130, -4130), H, ops=[door("P3", 1300, 900)]),
        iw("I1", "L1", (3200, 70), (3200, 7130), H, bearing=False, ops=[door("P4", 4500, 800)]),
    ]
    return proj("CT11", "Casa em T americana (rincões)", "wood", L1, walls, roofs=[
        {"id": "R1", "level": "L1", "kind": "gable", "ridge_axis": "x", "pitch_deg": 25,
         "outline": [[0, 0], [10800, 0], [10800, 7200], [0, 7200]]},
        {"id": "R2", "level": "L1", "kind": "gable", "ridge_axis": "y", "pitch_deg": 25, "ends": ["gable", "valley"],
         "outline": [[3600, -4200], [7200, -4200], [7200, 0], [3600, 0]]}])


def casa_U():
    """Casa em U: principal 2 águas + duas asas com rincão, pátio entre as asas."""
    H = 2700
    walls = [
        w("W", "L1", (70, -4130), (70, 7130), H, ops=[win("J1", 1500, 1200, 1200, 1000), win("J2", 7000, 1500, 1200, 1000)]),
        w("E", "L1", (11930, -4130), (11930, 7130), H, ops=[win("J3", 1500, 1200, 1200, 1000), win("J4", 7000, 1500, 1200, 1000)]),
        w("N", "L1", (70, 7130), (11930, 7130), H, ops=[win("J5", 2000, 1500, 1200, 1000), win("J6", 8000, 1500, 1200, 1000)]),
        w("S", "L1", (70, 70), (11930, 70), H, ops=[door("P1", 1400, 900), door("P2", 5000, 2000, 2100),
                                                     door("P3", 9700, 900)]),
        w("AS1", "L1", (70, -4130), (3530, -4130), H, ops=[win("J7", 1200, 1200, 1200, 1000)]),
        w("AI1", "L1", (3530, -4130), (3530, 70), H, ops=[win("J8", 1400, 1500, 1200, 1000)]),
        w("AS2", "L1", (8470, -4130), (11930, -4130), H, ops=[win("J9", 1200, 1200, 1200, 1000)]),
        w("AI2", "L1", (8470, -4130), (8470, 70), H, ops=[win("J10", 1400, 1500, 1200, 1000)]),
    ]
    return proj("CT12", "Casa em U (duas asas com rincão)", "wood", L1, walls, roofs=[
        {"id": "R1", "level": "L1", "kind": "gable", "ridge_axis": "x", "pitch_deg": 25,
         "outline": [[0, 0], [12000, 0], [12000, 7200], [0, 7200]]},
        {"id": "R2", "level": "L1", "kind": "gable", "ridge_axis": "y", "pitch_deg": 25, "ends": ["gable", "valley"],
         "outline": [[0, -4200], [3600, -4200], [3600, 0], [0, 0]]},
        {"id": "R3", "level": "L1", "kind": "gable", "ridge_axis": "y", "pitch_deg": 25, "ends": ["gable", "valley"],
         "outline": [[8400, -4200], [12000, -4200], [12000, 0], [8400, 0]]}])


def casa_americana():
    """Casa americana: principal 4 águas 25° + asa 2 águas 25° com rincão."""
    H = 2700
    walls = [
        w("N", "L1", (70, 8330), (11930, 8330), H, ops=[win("J1", 1500, 1500, 1200, 1000), win("J2", 8000, 1500, 1200, 1000)]),
        w("W", "L1", (70, 70), (70, 8330), H, ops=[win("J3", 1500, 1500, 1200, 1000)]),
        w("E", "L1", (11930, 70), (11930, 8330), H, ops=[door("P1", 3000, 900)]),
        w("S", "L1", (70, 70), (11930, 70), H, ops=[win("J4", 1300, 1500, 1200, 1000), door("P2", 5100, 1600),
                                                     win("J5", 8600, 1500, 1200, 1000)]),
        w("AW", "L1", (4270, -4730), (4270, 70), H, ops=[win("J6", 1800, 1200, 1200, 1000)]),
        w("AE", "L1", (7730, -4730), (7730, 70), H, ops=[win("J7", 1800, 1200, 1200, 1000)]),
        w("AS", "L1", (4270, -4730), (7730, -4730), H, ops=[door("P3", 1300, 900)]),
        iw("I1", "L1", (70, 4200), (11930, 4200), H, bearing=False, ops=[door("P4", 2000, 800), door("P5", 9000, 800)]),
    ]
    return proj("CT13", "Casa americana 4 águas com asa (rincões)", "wood", L1, walls, roofs=[
        {"id": "R1", "level": "L1", "kind": "hip", "ridge_axis": "x", "pitch_deg": 25,
         "outline": [[0, 0], [12000, 0], [12000, 8400], [0, 8400]]},
        {"id": "R2", "level": "L1", "kind": "gable", "ridge_axis": "y", "pitch_deg": 25, "ends": ["gable", "valley"],
         "outline": [[4200, -4800], [7800, -4800], [7800, 0], [4200, 0]]}])


def casa_parede_alta():
    """Meia-água 8° com parede alta: treliças apoiadas na parede baixa e penduradas na parede alta."""
    walls = [
        w("S", "L1", (70, 70), (8330, 70), 2700, ops=[win("J1", 500, 1600, 1500, 700), door("P1", 2600, 900),
                                                       win("J2", 5600, 2000, 1500, 700)]),
        w("N", "L1", (70, 5930), (8330, 5930), 3800, ops=[win("J3", 1200, 1200, 1000, 1000), win("J4", 5800, 1200, 1000, 1000)]),
        w("W", "L1", (70, 70), (70, 5930), 2700, ops=[win("J5", 2200, 1500, 1200, 1000)]),
        w("E", "L1", (8330, 70), (8330, 5930), 2700, ops=[]),
        iw("I1", "L1", (4200, 70), (4200, 5930), 2700, ops=[door("P2", 3600, 800)]),
    ]
    return proj("CT14", "Casa meia-água com parede alta", "wood", L1, walls, roofs=[
        {"id": "R1", "level": "L1", "kind": "mono", "ridge_axis": "x", "pitch_deg": 8, "support": "high_wall",
         "outline": [[0, 0], [8400, 0], [8400, 6000], [0, 6000]]}])


def casa_platibanda():
    """Casa com platibanda: telhado embutido 10% (5,7°), treliças penduradas por dentro das paredes."""
    H = 3850
    walls = rect("E", "L1", 0, 0, 9000, 7200, H, ops={
        "S": [win("J1", 700, 1600, 1400, 900), door("P1", 2700, 1000), win("J2", 5800, 2000, 1400, 900)],
        "N": [win("J3", 1200, 1500, 1200, 1000), win("J4", 6200, 1200, 1000, 1000)],
        "W": [win("J5", 2500, 1500, 1200, 1000)],
        "E": [win("J6", 2500, 1500, 1200, 1000)]})
    walls += [iw("I1", "L1", (4500, 70), (4500, 7130), 2700, ops=[door("P2", 4200, 800)])]
    return proj("CT15", "Casa com platibanda (telhado embutido 10%)", "wood", L1, walls, roofs=[
        {"id": "R1", "level": "L1", "kind": "mono", "ridge_axis": "x", "pitch_deg": 5.7, "support": "parapet",
         "bearing_height": 2700, "outline": [[0, 0], [9000, 0], [9000, 7200], [0, 7200]]}])


NEW2 = {"casa_em_T_rincao": casa_T, "casa_em_U_rincoes": casa_U, "casa_americana_4aguas_rincao": casa_americana,
        "casa_meia_agua_parede_alta": casa_parede_alta, "casa_platibanda": casa_platibanda}

if __name__ == "__main__":
    for name, fn in NEW2.items():
        (HERE / f"{name}.json").write_text(json.dumps(fn(), indent=1, ensure_ascii=False), encoding="utf-8")
        print("ok", name)


# ============================================================ caixa d'água (padrão Vigora)
def casa_caixa_dagua(model="BR_1000L", position=None):
    """Casa 90 m², 2 águas 30°, hall portante (shaft) no centro sob a cumeeira: caixa d'água no ático."""
    H = 2700
    walls = rect("E", "L1", 0, 0, 10800, 8400, H, ops={
        "S": [win("J1", 800, 1500, 1200, 1000), door("P1", 4600, 1000), win("J2", 7600, 1500, 1200, 1000)],
        "N": [win("J3", 800, 1500, 1200, 1000), win("J4", 5400, 600, 600, 1500), win("J5", 7600, 1500, 1200, 1000)],
        "W": [win("J6", 1200, 1200, 1200, 1000)],
        "E": [win("J7", 1200, 1200, 1200, 1000)]})
    walls += [
        # hall/shaft portante: duas paredes paralelas à cumeeira com vão livre de 1,41 m
        iw("H1", "L1", (70, 3450), (10730, 3450), H, bearing=True, ops=[door("P2", 1500, 800), door("P3", 6500, 800)]),
        iw("H2", "L1", (70, 4950), (10730, 4950), H, bearing=True, ops=[door("P4", 1500, 800), door("P5", 6500, 800),
                                                                       door("P6", 8800, 800)]),
        # parede portante do banheiro, perpendicular ao hall (interseção = ponto de inserção da caixa)
        iw("B1", "L1", (4200, 70), (4200, 3450), H, bearing=True, ops=[door("P7", 2200, 700)]),
        iw("B2", "L1", (4200, 4950), (4200, 8330), H, bearing=False, ops=[door("P8", 700, 800)]),
    ]
    tank = {"id": "CX1", "model": model, "level": "L1"}
    if position:
        tank["position"] = list(position)
    return proj("CT16", f"Casa com caixa d'água {model[3:]} no ático", "wood", L1, walls,
                roofs=[{"id": "R1", "level": "L1", "kind": "gable", "ridge_axis": "x", "pitch_deg": 30}]) | {"tanks": [tank]}


if __name__ == "__main__":
    (HERE / "casa_caixa_dagua.json").write_text(json.dumps(casa_caixa_dagua(), indent=1, ensure_ascii=False), encoding="utf-8")
    print("ok casa_caixa_dagua")


# ============================================================ varanda em pilares
def casa_varanda_pilares():
    """Casa 8,4 × 6,0 m, 2 águas 30°, com varanda de 3,6 × 2,4 m na frente: 2 águas perpendicular (rincão
    no principal), bordas apoiadas em 4 pilares + vigas de beiral."""
    H = 2700
    walls = rect("E", "L1", 0, 0, 8400, 6000, H, ops={
        "S": [win("J1", 600, 1200, 1200, 1000), door("P1", 2900, 900), win("J2", 6400, 1200, 1200, 1000)],
        "N": [win("J3", 1500, 1200, 1200, 1000), win("J4", 5500, 1200, 1200, 1000)]})
    walls += [iw("I1", "L1", (4200, 70), (4200, 5930), H, ops=[door("P2", 2500, 800)])]
    h_post = H - 235.0
    posts = [{"id": f"PL{i}", "level": "L1", "position": [x, y], "height": h_post}
             for i, (x, y) in enumerate([(2470, -2330), (2470, -600), (5930, -2330), (5930, -600)], 1)]
    roofs = [{"id": "R1", "level": "L1", "kind": "gable", "ridge_axis": "x", "pitch_deg": 30,
              "outline": [[0, 0], [8400, 0], [8400, 6000], [0, 6000]]},
             {"id": "R2", "level": "L1", "kind": "gable", "ridge_axis": "y", "pitch_deg": 30, "ends": ["gable", "valley"],
              "outline": [[2400, -2400], [6000, -2400], [6000, 0], [2400, 0]]}]
    return proj("CT17", "Casa com varanda em pilares", "wood", L1, walls, roofs=roofs) | {"posts": posts}


if __name__ == "__main__":
    (HERE / "casa_varanda_pilares.json").write_text(json.dumps(casa_varanda_pilares(), indent=1, ensure_ascii=False),
                                                    encoding="utf-8")
    print("ok casa_varanda_pilares")
