"""Atualização por diferença (seção 13): compara duas execuções pelo ID estável."""
from __future__ import annotations

from .model import Result

GEOM = ("item", "x0", "x1", "z0", "z1", "cut_length", "plies", "angle_a", "angle_b")


def diff(old: Result, new: Result) -> dict:
    a = {m.id: m for m in old.members}
    b = {m.id: m for m in new.members}
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = []
    for k in sorted(set(a) & set(b)):
        ma, mb = a[k], b[k]
        delta = {f: (getattr(ma, f), getattr(mb, f)) for f in GEOM if getattr(ma, f) != getattr(mb, f)}
        if delta:
            changed.append((k, delta))
    pa = {p.id: p.signature for p in old.panels}
    pb = {p.id: p.signature for p in new.panels}
    panels_changed = sorted(k for k in set(pa) | set(pb) if pa.get(k) != pb.get(k))
    return {"added": added, "removed": removed, "changed": changed, "panels_changed": panels_changed,
            "unchanged": len(set(a) & set(b)) - len(changed)}
