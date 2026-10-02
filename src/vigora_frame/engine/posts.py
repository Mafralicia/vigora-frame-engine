"""Varanda/alpendre: borda do telhado apoiada em pilares + viga de beiral (no lugar de uma parede portante).

Pilar: pilarete composto 3 × 38×140 (wood) do piso ao fundo da viga. Viga de beiral: 2 × 38×235 ao longo de
toda a borda do telhado, com o topo na cota do topo das paredes (as treliças apoiam nela como numa parede).
Vão entre pilares e balanço nas pontas verificados (V-089). Valores de REFERÊNCIA: aprovação do engenheiro.
"""
from __future__ import annotations

from .context import Ctx

POST_ITEM, POST_PLIES = "W-38x140", 3
BEAM_ITEM, BEAM_PLIES = "W-38x235", 2
MAX_POST_SPAN = 3000.0        # vão máximo entre pilares para a viga 2 × 38×235 (rascunho)
MAX_CANTILEVER = 600.0        # balanço máximo da viga além do último pilar
LINE_TOL = 200.0              # distância máxima do centro do pilar à borda do telhado (mm)


def post_line_support(ctx: Ctx, rs, rid: str, axis: str, face: float, inward: int, along: tuple[float, float],
                      lv_elev: float):
    """Pilares sob a borda 'face' do telhado (eixo 'axis' = direção da cumeeira). Cria pilares e viga uma vez.
    Retorna a altura (mm, a partir do piso do nível) do topo da viga, ou None se não há linha de pilares."""
    posts = []
    for p in ctx.project.posts:
        if p.level != rs.level:
            continue
        c = p.position[1] if axis == "x" else p.position[0]
        a = p.position[0] if axis == "x" else p.position[1]
        if -5 <= (c - face) * inward <= LINE_TOL and along[0] - 300 <= a <= along[1] + 300:
            posts.append((a, c, p))
    if len(posts) < 2:
        return None
    posts.sort(key=lambda t: t[0])
    t = ctx.cat.face(POST_ITEM)
    d_post = ctx.cat.depth(POST_ITEM)
    d_beam = ctx.cat.depth(BEAM_ITEM)
    hs = {round(p.height) for _, _, p in posts}
    if len(hs) > 1:
        ctx.issue("V-089", "error", rid, f"pilares da varanda com alturas diferentes ({min(hs)} a {max(hs)} mm)")
    h_post = min(p.height for _, _, p in posts)
    key = (rs.level, axis, round(face), round(along[0]), round(along[1]))
    if key in ctx.post_lines:
        return ctx.post_lines[key]
    gaps = [b[0] - a[0] for a, b in zip(posts, posts[1:])]
    if gaps and max(gaps) > MAX_POST_SPAN + 0.5:
        ctx.issue("V-089", "error", rid, f"vão entre pilares {max(gaps):.0f} mm > {MAX_POST_SPAN:.0f} mm para a viga de "
                                         "beiral 2 × 38×235: acrescente um pilar")
    for cant in (posts[0][0] - along[0], along[1] - posts[-1][0]):
        if cant > MAX_CANTILEVER + 0.5:
            ctx.issue("V-089", "warning", rid, f"viga de beiral em balanço de {cant:.0f} mm além do último pilar "
                                               f"(máx. {MAX_CANTILEVER:.0f})")
    lid = f"{ctx.pfx}-{rs.level}-{rid.split('-')[-1]}-PL{len(ctx.post_lines) + 1:02d}"
    c_line = face + inward * (d_post / 2)            # face externa do pilar e da viga alinhadas à borda do telhado
    w_post = t * POST_PLIES
    for i, (a, c, p) in enumerate(posts, 1):
        x0, x1, y0, y1 = (a - w_post / 2, a + w_post / 2, c_line - d_post / 2, c_line + d_post / 2) if axis == "x" else \
            (c_line - d_post / 2, c_line + d_post / 2, a - w_post / 2, a + w_post / 2)
        m = ctx.new_member("POST", POST_ITEM, rs.level, "roof", lid, frame="plan", x0=a if axis == "x" else c_line,
                           x1=a if axis == "x" else c_line, z0=c_line if axis == "x" else a,
                           z1=c_line if axis == "x" else a, orientation="V", plies=POST_PLIES,
                           cut_length=round(h_post, 1), rule="posts.post",
                           note=f"pilar {p.id}: {POST_PLIES} × {POST_ITEM} pregados, do piso ao fundo da viga")
        m.id = f"{lid}-POST-{i:02d}"
        ctx.members.append(m)
        ctx.hw("CHAPA-BASE-PILAR", 1, f"{lid} base metálica do pilar {p.id}")
        ctx.hw("CHUMBADOR-M12", 2, f"{lid} chumbadores da base do pilar {p.id}")
        ctx.hw("CONECTOR-ARRANC-H1", 2, f"{lid} pilar {p.id} × viga de beiral")
    a0, a1 = along
    x0, x1, y0, y1 = (a0, a1, c_line - t * BEAM_PLIES / 2, c_line + t * BEAM_PLIES / 2) if axis == "x" else \
        (c_line - t * BEAM_PLIES / 2, c_line + t * BEAM_PLIES / 2, a0, a1)
    ctx.placements[lid] = {"z": lv_elev + h_post, "depth": d_beam}
    m = ctx.new_member("EAVE_BEAM", BEAM_ITEM, rs.level, "eave", lid, frame="plan", x0=x0, x1=x1, z0=y0, z1=y1,
                       orientation="H", plies=BEAM_PLIES, cut_length=round(a1 - a0, 1), depth=d_beam,
                       rule="posts.beam", note=f"viga de beiral {BEAM_PLIES} × {BEAM_ITEM} sobre {len(posts)} pilares")
    m.id = f"{lid}-EAVE_BEAM-01"
    ctx.members.append(m)
    top = h_post + d_beam
    ctx.post_lines[key] = top
    ctx.issue("V-000", "info", rid, f"borda do telhado apoiada em {len(posts)} pilares + viga de beiral "
                                    f"(topo a {top:.0f} mm)")
    return top
