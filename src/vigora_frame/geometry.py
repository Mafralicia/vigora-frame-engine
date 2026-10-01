"""Funções geométricas (planta 2D, facetas de curva, arcos). Unidades: mm."""
from __future__ import annotations

import math

Vec = tuple[float, float]


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1])


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])


def mul(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k)


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1]


def cross(a: Vec, b: Vec) -> float:
    return a[0] * b[1] - a[1] * b[0]


def length(a: Vec) -> float:
    return math.hypot(a[0], a[1])


def unit(a: Vec) -> Vec:
    n = length(a)
    return (a[0] / n, a[1] / n)


def dist(a: Vec, b: Vec) -> float:
    return length(sub(a, b))


def project_param(p: Vec, a: Vec, b: Vec) -> tuple[float, float]:
    """Retorna (t em mm ao longo de a->b, distância perpendicular)."""
    d = sub(b, a)
    L = length(d)
    u = (d[0] / L, d[1] / L)
    ap = sub(p, a)
    t = dot(ap, u)
    perp = abs(cross(u, ap))
    return t, perp


def angle_between_deg(u: Vec, v: Vec) -> float:
    c = max(-1.0, min(1.0, dot(unit(u), unit(v))))
    return math.degrees(math.acos(c))


# ------------------------------------------------------------ curvas (A7.2)
def sagitta(radius: float, chord: float) -> float:
    return radius - math.sqrt(radius ** 2 - (chord / 2) ** 2)


def facet_angle_deg(radius: float, chord: float) -> float:
    return math.degrees(2 * math.asin(chord / (2 * radius)))


def max_chord_for_sagitta(radius: float, s_max: float) -> float:
    return 2 * math.sqrt(2 * radius * s_max - s_max ** 2)


def facet_arc(center: Vec, radius: float, a0_deg: float, a1_deg: float,
              max_chord: float, max_sagitta: float) -> list[tuple[Vec, Vec]]:
    """Divide o arco em facetas iguais que respeitam corda e flecha máximas."""
    c_lim = min(max_chord, max_chord_for_sagitta(radius, max_sagitta))
    sweep = math.radians(a1_deg - a0_deg)
    arc_len = abs(sweep) * radius
    # ângulo máximo por faceta a partir da corda limite
    dth_max = 2 * math.asin(min(1.0, c_lim / (2 * radius)))
    n = max(1, math.ceil(abs(sweep) / dth_max - 1e-9))
    pts = []
    for i in range(n + 1):
        a = math.radians(a0_deg) + sweep * i / n
        pts.append((center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)))
    return [(pts[i], pts[i + 1]) for i in range(n)]


# ------------------------------------------------------------ arcos (A7.4)
def arch_radius(span: float, rise: float) -> float:
    return span ** 2 / (8 * rise) + rise / 2


def arch_filler_polygons(span: float, rise: float, spring_z: float, n: int = 64) -> list[list[Vec]]:
    """Enchimento do tímpano: duas peças (esquerda e direita) entre o retângulo e o arco.

    Coordenadas locais do vão: x = 0 na lateral esquerda, z absoluto.
    """
    R = arch_radius(span, rise)
    cx = span / 2
    cz = spring_z + rise - R
    top = spring_z + rise

    def arc_z(x):
        return cz + math.sqrt(max(R ** 2 - (x - cx) ** 2, 0.0))

    left = [(0.0, spring_z)]
    for i in range(n + 1):
        x = cx * i / n
        left.append((x, arc_z(x)))
    left += [(cx, top), (0.0, top)]
    right = [(span, spring_z), (span, top), (cx, top)]
    for i in range(n + 1):
        x = cx + cx * i / n
        right.append((x, arc_z(x)))
    return [left, right]


def seg_intersection(p1: Vec, p2: Vec, p3: Vec, p4: Vec):
    """Interseção de retas p1p2 e p3p4 (retorna ponto ou None se paralelas)."""
    d1 = sub(p2, p1)
    d2 = sub(p4, p3)
    den = cross(d1, d2)
    if abs(den) < 1e-12:
        return None
    t = cross(sub(p3, p1), d2) / den
    return add(p1, mul(d1, t))
