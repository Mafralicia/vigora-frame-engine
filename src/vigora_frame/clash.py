"""Conflitos 3D entre peças (madeira/aço): toda peça contra toda peça do modelo, de qualquer sistema.

Cada peça é um prisma (perfil plano extrudado, igual ao que vai para o Revit). Teste exato por eixos
separadores (SAT) entre prismas convexos; perfis não convexos são divididos em triângulos. Peças que só
encostam (apoio, pregação) não são conflito: só conta penetração maior que a tolerância (1 mm).
"""
from __future__ import annotations

import numpy as np

TOL = 1.0          # mm de penetração tolerada (apoio/encosto)


def _convex_parts(profile):
    """Perfil 3D plano -> lista de perfis convexos (o próprio, ou triângulos se não for convexo)."""
    from shapely.geometry import Polygon
    from shapely.ops import triangulate
    P = np.array(profile, float)
    if len(P) <= 3:
        return [P]
    o = P[0]
    u = P[1] - P[0]
    u /= np.linalg.norm(u) or 1.0
    n = np.zeros(3)
    for k in range(2, len(P)):
        n = np.cross(P[1] - P[0], P[k] - P[0])
        if np.linalg.norm(n) > 1e-6:
            break
    n /= np.linalg.norm(n) or 1.0
    v = np.cross(n, u)
    uv = [((p - o) @ u, (p - o) @ v) for p in P]
    poly = Polygon(uv)
    if not poly.is_valid or poly.area < 1e-6:
        return [P]
    if poly.convex_hull.area - poly.area < 1e-3 * max(poly.area, 1.0):
        return [P]
    out = []
    for t in triangulate(poly):
        if poly.contains(t.representative_point()):
            out.append(np.array([o + a * u + b * v for a, b in list(t.exterior.coords)[:3]]))
    return out or [P]


class _Prism:
    __slots__ = ("V", "axes", "lo", "hi", "sid", "role", "parent")

    def __init__(self, P, e, sid, role, parent):
        e = np.array(e, float)
        self.V = np.vstack([P, P + e])
        edges = [P[(i + 1) % len(P)] - P[i] for i in range(len(P))] + [e]
        n = np.cross(edges[0], edges[1] if len(P) > 2 else e)
        axes = [n] + [np.cross(ed, e) for ed in edges[:-1]]
        self.axes = (axes, edges)
        self.lo, self.hi = self.V.min(0), self.V.max(0)
        self.sid, self.role, self.parent = sid, role, parent


def _depth(a: _Prism, b: _Prism) -> float:
    """Penetração mínima entre dois prismas convexos (<= 0: separados ou só encostados)."""
    axes = list(a.axes[0]) + list(b.axes[0])
    for ea in a.axes[1]:
        for eb in b.axes[1]:
            axes.append(np.cross(ea, eb))
    best = np.inf
    for ax in axes:
        L = np.linalg.norm(ax)
        if L < 1e-9:
            continue
        ax = ax / L
        pa, pb = a.V @ ax, b.V @ ax
        ov = min(pa.max(), pb.max()) - max(pa.min(), pb.min())
        if ov <= TOL:
            return ov
        best = min(best, ov)
    return best


def find_clashes(solids, skip_groups=("tank",), tol=TOL, limit=200):
    """Pares de peças que se penetram mais que 'tol'. solids: lista de revit_solids()['solids']."""
    global TOL
    TOL = tol
    prisms = []
    for s in solids:
        if s.get("group") in skip_groups:
            continue
        for part in _convex_parts(s["profile"]):
            prisms.append(_Prism(part, s["extrude"], s["id"], s.get("role", ""), s.get("parent", "")))
    order = sorted(range(len(prisms)), key=lambda i: prisms[i].lo[0])
    out, seen = [], set()
    for k, i in enumerate(order):
        a = prisms[i]
        for j in order[k + 1:]:
            b = prisms[j]
            if b.lo[0] >= a.hi[0] - tol:
                break
            if a.sid == b.sid:
                continue
            if (b.lo[1] >= a.hi[1] - tol or a.lo[1] >= b.hi[1] - tol or
                    b.lo[2] >= a.hi[2] - tol or a.lo[2] >= b.hi[2] - tol):
                continue
            key = tuple(sorted((a.sid, b.sid)))
            if key in seen:
                continue
            d = _depth(a, b)
            if d > tol:
                seen.add(key)
                out.append({"a": key[0], "b": key[1], "depth": round(float(d), 1),
                            "roles": tuple(sorted((a.role, b.role)))})
                if len(out) >= limit:
                    return out
    return out


def add_clash_issues(res, limit=50):
    """Acrescenta ao resultado um erro V-060 por par de peças que se penetram (todas contra todas, em 3D)."""
    from .model import Issue
    from .revit_bridge import revit_solids
    found = find_clashes(revit_solids(res)["solids"], limit=limit)
    for c in found:
        res.issues.append(Issue(code="V-060", severity="error", element=c["a"],
                                message=f"conflito 3D: {c['a']} penetra {c['depth']:.0f} mm em {c['b']}"))
    st = res.stats.setdefault("issues", {})
    if found:
        st["error"] = st.get("error", 0) + len(found)
    else:
        res.issues.append(Issue(code="V-000", severity="info", element="modelo",
                                message="nenhuma peça penetra outra (verificação 3D de todas as peças)"))
        st["info"] = st.get("info", 0) + 1
    return found
