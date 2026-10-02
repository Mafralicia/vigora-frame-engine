"""Pranchas técnicas em PDF (seção 12) com matplotlib.

Cada página A3 paisagem tem carimbo com projeto, ruleset, execução e status.
Execuções sem aprovação levam a marca d'água RASCUNHO.
"""
from __future__ import annotations

import math
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MPoly
from matplotlib.patches import Rectangle

from ..model import Result

A3 = (16.54, 11.69)
COLORS = {"POST": "#7B3F1D", "EAVE_BEAM": "#9C5A2E", "TANK_BEAM": "#7B3F1D", "WATER_TANK": "#2F6FA8", "TANK_TRAY": "#9EC5E4", "TANK_DECK": "#C9A36B",
          "LEDGER": "#8D6E63", 
    "BOTTOM_PLATE": "#8d6e63", "TOP_PLATE": "#8d6e63", "CAP_PLATE": "#bcaaa4",
    "STUD": "#f3d9a4", "STUD_END": "#e0b96a", "SHEET_STUD": "#f7e2b8", "NAILER": "#f7e2b8", "BACKER": "#d8a657",
    "KING": "#c98b3c", "JACK": "#e38f4d", "HEADER": "#b5532b", "SILL": "#a1887f", "CRIPPLE": "#f0c27b",
    "BLOCK": "#90a4ae", "PACKER": "#ef9a9a", "ARCH_FILLER": "#ce93d8", "STRAP": "#607d8b",
    "BRACE_STRAP": "#455a64", "TOP_CHORD": "#c98b3c", "BOTTOM_CHORD": "#8d6e63", "WEB": "#f0c27b",
    "GABLE_STUD": "#f3d9a4", "JOIST": "#f3d9a4", "TAIL_JOIST": "#f0c27b", "TRIMMER": "#c98b3c",
    "FLOOR_HEADER": "#b5532b", "RIM": "#8d6e63", "RIM_SIDE": "#8d6e63", "BRIDGING": "#90a4ae",
}
LABEL = {"STUD": "montante", "STUD_END": "montante de borda", "SHEET_STUD": "montante de junta de placa",
         "NAILER": "apoio de placa", "BACKER": "reforço de canto/T", "KING": "montante king", "JACK": "ombreira (jack)",
         "HEADER": "verga", "SILL": "peitoril", "CRIPPLE": "montante curto", "BLOCK": "bloqueio",
         "BOTTOM_PLATE": "placa inferior", "TOP_PLATE": "placa superior", "PACKER": "calço",
         "ARCH_FILLER": "enchimento do arco (CNC)", "STRAP": "fita de travamento", "BRACE_STRAP": "fita em X"}


def _frame(fig, res: Result, title: str, page: int, total: int | None = None):
    fig.text(0.02, 0.975, "VIGORA", fontsize=16, weight="bold", color="#1b1b1b", va="top")
    fig.text(0.085, 0.972, "Frame Engine", fontsize=10, color="#8a5a2b", va="top")
    fig.text(0.5, 0.975, title, fontsize=13, weight="bold", ha="center", va="top")
    fig.add_artist(plt.Line2D([0.02, 0.98], [0.945, 0.945], color="#333", lw=0.8))
    fig.add_artist(plt.Line2D([0.02, 0.98], [0.055, 0.055], color="#333", lw=0.8))
    status = "APROVADO" if res.ruleset_approved else "RASCUNHO - NÃO LIBERADO PARA FÁBRICA"
    fig.text(0.02, 0.035, f"{res.project} · {res.project_name} · sistema {res.system} · ruleset {res.ruleset}",
             fontsize=8)
    fig.text(0.02, 0.018, f"execução {res.run_id} · entrada {res.input_hash} · unidades mm", fontsize=7, color="#555")
    fig.text(0.98, 0.035, status, fontsize=9, ha="right", weight="bold",
             color="#2e7d32" if res.ruleset_approved else "#c62828")
    fig.text(0.98, 0.018, f"folha {page}" + (f"/{total}" if total else ""), fontsize=8, ha="right")
    if not res.ruleset_approved:
        fig.text(0.5, 0.5, "RASCUNHO", fontsize=110, color="#c62828", alpha=0.06, ha="center", va="center",
                 rotation=25, weight="bold")


def _cover(pdf, res: Result, q: dict, page: int):
    fig = plt.figure(figsize=A3)
    _frame(fig, res, "Resumo do projeto", page)
    ax = fig.add_axes([0.04, 0.08, 0.44, 0.82])
    ax.axis("off")
    st = res.stats
    sev = st["issues"]
    lines = [
        ("Projeto", f"{res.project} — {res.project_name}"),
        ("Sistema / ruleset", f"{res.system} / {res.ruleset}"),
        ("Status", "aprovado" if res.ruleset_approved else "RASCUNHO (ruleset e catálogo sem aprovação)"),
        ("Painéis", f"{st['panels']} ({st['unique_panels']} diferentes)"),
        ("Peças", f"{st['members']} ({st['special_members']} especiais)"),
        ("Ligações", f"{st['connections']}"),
        ("Placas posicionadas", f"{st['sheets']}"),
        ("Treliças", f"{st['trusses']}"),
        ("Metros lineares", f"{q['summary']['linear_m']:.1f} m"),
        ("Barras a comprar", f"{q['summary']['bars']}"),
        ("Aproveitamento de barras", f"{q['summary']['yield'] * 100:.1f}%"),
        ("Placas a comprar", f"{q['summary']['sheets']}"),
        ("Peso das peças lineares", f"{q['summary']['kg_linear']:.0f} kg"),
        ("Erros / avisos / informações", f"{sev.get('error', 0)} / {sev.get('warning', 0)} / {sev.get('info', 0)}"),
    ]
    y = 0.97
    for k, v in lines:
        ax.text(0.0, y, k, fontsize=11, color="#555", transform=ax.transAxes, va="top")
        ax.text(0.42, y, v, fontsize=11, weight="bold", transform=ax.transAxes, va="top")
        y -= 0.062
    ax2 = fig.add_axes([0.52, 0.08, 0.45, 0.82])
    ax2.axis("off")
    ax2.text(0, 1, "Índice de folhas", fontsize=12, weight="bold", transform=ax2.transAxes, va="top")
    idx = ["1  Resumo", "2  Planta de painéis", "3  Vista 3D do framing", "4+ Elevações de painéis",
           "   Treliças por marca", "   Entrepiso (se houver)", "   Relatório de validação"]
    for i, t in enumerate(idx):
        ax2.text(0, 0.93 - i * 0.05, t, fontsize=10, transform=ax2.transAxes, va="top")
    ax2.text(0, 0.5, "Legenda de cores", fontsize=12, weight="bold", transform=ax2.transAxes, va="top")
    for i, (k, v) in enumerate(list(LABEL.items())):
        yy = 0.45 - (i % 9) * 0.045
        xx = 0 if i < 9 else 0.5
        ax2.add_patch(Rectangle((xx, yy - 0.025), 0.04, 0.03, color=COLORS.get(k, "#ccc"), transform=ax2.transAxes))
        ax2.text(xx + 0.06, yy - 0.01, v, fontsize=9, transform=ax2.transAxes, va="center")
    pdf.savefig(fig)
    plt.close(fig)


def _plan(pdf, res: Result, page: int):
    levels = sorted(res.stats["levels"].items(), key=lambda kv: kv[1]["elevation"])
    fig = plt.figure(figsize=A3)
    _frame(fig, res, "Planta de painéis", page)
    n = len(levels)
    for i, (lid, lv) in enumerate(levels):
        ax = fig.add_axes([0.04 + i * (0.93 / n), 0.09, 0.93 / n - 0.02, 0.82])
        ax.set_title(f"{lv['name']} ({lid})", fontsize=11)
        ax.set_aspect("equal")
        ax.axis("off")
        for p in [p for p in res.panels if p.level == lid]:
            ox, oy, _ = p.origin
            dx, dy = p.direction
            x1, y1 = ox + dx * p.length, oy + dy * p.length
            ax.plot([ox, x1], [oy, y1], color="#c98b3c" if not p.special else "#8e24aa", lw=5, solid_capstyle="butt")
            ax.plot([ox], [oy], marker="|", color="k", ms=10)
            mx, my = (ox + x1) / 2, (oy + y1) / 2
            nx, ny = -dy, dx
            ax.text(mx + nx * 260, my + ny * 260, p.id.split("-", 2)[-1].replace(f"{lid}-", ""), fontsize=6,
                    ha="center", va="center", rotation=math.degrees(math.atan2(dy, dx)) % 180 - (180 if math.degrees(math.atan2(dy, dx)) % 180 > 90 else 0))
        for m in res.members:
            if m.level == lid and m.role == "COLUMN":
                ax.plot([m.x0], [m.z0], "s", color="#4e342e", ms=8)
                ax.text(m.x0 + 150, m.z0 + 150, m.id.split("-")[-3], fontsize=7)
    pdf.savefig(fig)
    plt.close(fig)


def _panel_global_unused(p, x, z):
    ox, oy, oz = p.origin
    dx, dy = p.direction
    return ox + dx * x, oy + dy * x, oz + z


def _iso(pdf, res: Result, page: int):
    """Vista 3D com os mesmos sólidos enviados ao Revit."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from ..revit_bridge import revit_solids
    fig = plt.figure(figsize=A3)
    _frame(fig, res, "Vista 3D do framing (mesmos sólidos enviados ao Revit)", page)
    ax = fig.add_axes([0.02, 0.07, 0.96, 0.86], projection="3d")
    faces, cols = [], []
    for s in revit_solids(res)["solids"]:
        p, e = s["profile"], s["extrude"]
        q = [[a[0] + e[0], a[1] + e[1], a[2] + e[2]] for a in p]
        faces += [p, q] + [[p[i], p[(i + 1) % len(p)], q[(i + 1) % len(p)], q[i]] for i in range(len(p))]
        cols += [COLORS.get(s["role"], "#ccc")] * (2 + len(p))
    if faces:
        ax.add_collection3d(Poly3DCollection(faces, facecolors=cols, edgecolors="#5d4037", linewidths=0.05))
        xs = [v[0] for f in faces for v in f]
        ys = [v[1] for f in faces for v in f]
        zs = [v[2] for f in faces for v in f]
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(ys), max(ys))
        ax.set_zlim(min(zs), max(zs))
        ax.set_box_aspect((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    ax.view_init(elev=22, azim=-55)
    ax.set_axis_off()
    pdf.savefig(fig)
    plt.close(fig)


def _dim_chain(ax, xs, y, color="#333"):
    xs = sorted(set(round(x, 1) for x in xs))
    for a, b in zip(xs, xs[1:]):
        ax.annotate("", xy=(a, y), xytext=(b, y), arrowprops=dict(arrowstyle="-", color=color, lw=0.5))
        ax.plot([a, a], [y - 25, y + 25], color=color, lw=0.5)
        if b - a > 60:
            ax.text((a + b) / 2, y + 35, f"{b - a:.0f}", fontsize=5.5, ha="center", va="bottom")
    if xs:
        ax.plot([xs[-1], xs[-1]], [y - 25, y + 25], color=color, lw=0.5)


def panel_figure(res: Result, pid: str, page: int = 0):
    p = next(x for x in res.panels if x.id == pid)
    ms = [m for m in res.members if m.parent == pid]
    shs = [s for s in res.sheets if s.parent == pid]
    fig = plt.figure(figsize=A3)
    _frame(fig, res, f"Elevação do painel {pid}", page)
    ax = fig.add_axes([0.05, 0.12, 0.66, 0.78])
    ax.set_aspect("equal")
    for m in sorted(ms, key=lambda m: m.plane == "face"):
        c = COLORS.get(m.role, "#ccc")
        if m.polygon:
            ax.add_patch(MPoly(m.polygon, closed=True, fc=c, ec="#333", lw=0.4,
                               alpha=0.55 if m.plane == "face" else 1))
        else:
            ax.add_patch(Rectangle((m.x0, m.z0), m.x1 - m.x0, max(m.z1 - m.z0, 6), fc=c, ec="#333", lw=0.4,
                                   alpha=0.6 if m.plane == "face" else 1))
    for s in shs:
        ax.add_patch(Rectangle((s.x0, s.z0), s.x1 - s.x0, s.z1 - s.z0, fill=False, ec="#1565c0", lw=0.6, ls="--"))
        for c in s.cutouts:
            ax.add_patch(Rectangle((c[0], c[2]), c[1] - c[0], c[3] - c[2], fill=False, ec="#1565c0", lw=0.3, hatch="//"))
    # etiquetas curtas
    for m in ms:
        if m.orientation == "V" and m.z1 - m.z0 > 400:
            ax.text((m.x0 + m.x1) / 2, (m.z0 + m.z1) / 2, m.id.split("-")[-2][:2] + m.id.split("-")[-1],
                    fontsize=4.5, rotation=90, ha="center", va="center")
        elif m.role == "HEADER":
            ax.text((m.x0 + m.x1) / 2, (m.z0 + m.z1) / 2, f"verga {m.plies}x {m.item} L={m.cut_length:.0f}",
                    fontsize=6, ha="center", va="center", color="white", weight="bold")
    verts = [m for m in ms if m.orientation == "V" and m.plane == "core" and m.role != "CRIPPLE"]
    _dim_chain(ax, [0] + [(m.x0 + m.x1) / 2 for m in verts] + [p.length], -180)
    _dim_chain(ax, [0, p.length], -380)
    ax.text(p.length / 2, -330, f"{p.length:.0f}", fontsize=9, ha="center", weight="bold")
    ax.plot([-250, -250], [0, p.height], color="#333", lw=0.6)
    ax.text(-300, p.height / 2, f"{p.height:.0f}", rotation=90, fontsize=9, ha="right", va="center", weight="bold")
    ax.set_xlim(-600, p.length + 200)
    ax.set_ylim(-520, p.height + 200)
    ax.axis("off")
    ax.text(0, p.height + 90, "vista pela face externa · placas estruturais em azul tracejado", fontsize=7, color="#555")
    # tabela de peças
    tx = fig.add_axes([0.73, 0.12, 0.25, 0.78])
    tx.axis("off")
    cnt = defaultdict(lambda: [0, 0.0, ""])
    for m in ms:
        k = (m.role, m.item, round(m.cut_length))
        cnt[k][0] += m.plies
        cnt[k][2] = m.item
    rows = sorted(cnt.items(), key=lambda kv: (kv[0][0], -kv[0][2]))
    tx.text(0, 1, f"Painel {pid.split('-', 2)[-1]}", fontsize=10, weight="bold", va="top", transform=tx.transAxes)
    info = [f"tipo {p.wall_type} · {p.length:.0f} x {p.height:.0f} mm", f"peso estimado {p.weight_kg:.0f} kg",
            f"{len(ms)} peças · {len(shs)} placas · assinatura {p.signature}"]
    for i, t in enumerate(info):
        tx.text(0, 0.965 - i * 0.022, t, fontsize=7.5, va="top", transform=tx.transAxes)
    y = 0.88
    tx.text(0, y, "função", fontsize=7, weight="bold", transform=tx.transAxes)
    tx.text(0.42, y, "item", fontsize=7, weight="bold", transform=tx.transAxes)
    tx.text(0.78, y, "corte", fontsize=7, weight="bold", transform=tx.transAxes)
    tx.text(0.93, y, "qtd", fontsize=7, weight="bold", transform=tx.transAxes)
    for (role, item, L), (n, _, _) in rows[:48]:
        y -= 0.0165
        tx.text(0, y, LABEL.get(role, role.lower()), fontsize=6.5, transform=tx.transAxes)
        tx.text(0.42, y, item, fontsize=6.5, transform=tx.transAxes)
        tx.text(0.78, y, f"{L}", fontsize=6.5, transform=tx.transAxes)
        tx.text(0.93, y, f"{n}", fontsize=6.5, transform=tx.transAxes)
    if len(rows) > 48:
        tx.text(0, y - 0.02, f"... +{len(rows) - 48} linhas na planilha", fontsize=6.5, transform=tx.transAxes)
    return fig


def _truss_pages(pdf, res: Result, page: int) -> int:
    for tm in res.trusses:
        if not tm.member_ids:
            continue
        ms = [m for m in res.members if m.id in set(tm.member_ids)]
        fig = plt.figure(figsize=A3)
        _frame(fig, res, f"Treliça {tm.mark} — {tm.type} — {tm.count} unidades", page)
        ax = fig.add_axes([0.04, 0.3, 0.92, 0.6])
        ax.set_aspect("equal")
        for m in ms:
            ax.add_patch(MPoly(m.polygon, closed=True, fc=COLORS.get(m.role, "#ccc"), ec="#333", lw=0.6))
            cx = sum(p[0] for p in m.polygon) / len(m.polygon)
            cy = sum(p[1] for p in m.polygon) / len(m.polygon)
            ax.text(cx, cy, m.id.split("-")[-1] if m.role == "WEB" else "", fontsize=6, ha="center")
        xs = [p[0] for m in ms for p in m.polygon]
        ys = [p[1] for m in ms for p in m.polygon]
        ax.set_xlim(min(xs) - 200, max(xs) + 200)
        ax.set_ylim(min(ys) - 300, max(ys) + 200)
        ax.axis("off")
        _dim_chain(ax, [0, tm.span], min(ys) - 200)
        ax.text(tm.span / 2, min(ys) - 150, f"vão {tm.span:.0f}", ha="center", fontsize=9, weight="bold")
        tx = fig.add_axes([0.04, 0.07, 0.92, 0.2])
        tx.axis("off")
        tx.text(0, 1, f"inclinação {tm.pitch_deg}° · altura {tm.height:.0f} mm · peças (comprimento ponta a ponta):",
                fontsize=9, weight="bold", va="top", transform=tx.transAxes)
        for i, m in enumerate(sorted(ms, key=lambda m: m.id)):
            col, row = divmod(i, 7)
            tx.text(col * 0.25, 0.82 - row * 0.12, f"{m.id.split('-', 4)[-1]}: {m.item}  L={m.cut_length:.0f}  "
                                                    f"{m.angle_a:.0f}°/{m.angle_b:.0f}°", fontsize=7, transform=tx.transAxes)
        pdf.savefig(fig)
        plt.close(fig)
        page += 1
    return page


def _floor_pages(pdf, res: Result, page: int) -> int:
    floors = sorted({m.parent for m in res.members if m.group == "floor"})
    for fid in floors:
        ms = [m for m in res.members if m.parent == fid]
        fig = plt.figure(figsize=A3)
        _frame(fig, res, f"Entrepiso {fid}", page)
        ax = fig.add_axes([0.04, 0.08, 0.92, 0.84])
        ax.set_aspect("equal")
        for m in ms:
            ax.add_patch(Rectangle((m.x0, m.z0), m.x1 - m.x0, m.z1 - m.z0, fc=COLORS.get(m.role, "#ccc"), ec="#333", lw=0.3))
        for s in [s for s in res.sheets if s.parent == fid]:
            ax.add_patch(Rectangle((s.x0, s.z0), s.x1 - s.x0, s.z1 - s.z0, fill=False, ec="#1565c0", lw=0.4, ls="--"))
        xs = [m.x0 for m in ms] + [m.x1 for m in ms]
        ys = [m.z0 for m in ms] + [m.z1 for m in ms]
        ax.set_xlim(min(xs) - 300, max(xs) + 300)
        ax.set_ylim(min(ys) - 300, max(ys) + 300)
        ax.axis("off")
        cnt = defaultdict(int)
        for m in ms:
            cnt[m.role] += 1
        ax.text(min(xs), max(ys) + 150, " · ".join(f"{k.lower()}: {v}" for k, v in sorted(cnt.items())), fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)
        page += 1
    return page


def _issues_page(pdf, res: Result, page: int):
    items = sorted(res.issues, key=lambda i: ({"error": 0, "warning": 1, "info": 2}[i.severity], i.code))
    per = 42
    for k in range(0, max(1, len(items)), per):
        fig = plt.figure(figsize=A3)
        _frame(fig, res, "Relatório de validação", page)
        ax = fig.add_axes([0.03, 0.07, 0.94, 0.86])
        ax.axis("off")
        for i, it in enumerate(items[k:k + per]):
            col = {"error": "#c62828", "warning": "#ef6c00", "info": "#2e7d32"}[it.severity]
            ax.text(0, 1 - i * 0.0235, f"{it.code}", color=col, fontsize=8, weight="bold", transform=ax.transAxes, va="top")
            ax.text(0.05, 1 - i * 0.0235, it.severity, color=col, fontsize=8, transform=ax.transAxes, va="top")
            ax.text(0.11, 1 - i * 0.0235, it.element[:40], fontsize=8, transform=ax.transAxes, va="top")
            ax.text(0.36, 1 - i * 0.0235, it.message[:150], fontsize=8, transform=ax.transAxes, va="top")
        pdf.savefig(fig)
        plt.close(fig)
        page += 1
    return page


def write_drawings(res: Result, q: dict, path: str) -> int:
    with PdfPages(path) as pdf:
        page = 1
        _cover(pdf, res, q, page)
        page += 1
        _plan(pdf, res, page)
        page += 1
        _iso(pdf, res, page)
        page += 1
        for p in res.panels:
            fig = panel_figure(res, p.id, page)
            pdf.savefig(fig)
            plt.close(fig)
            page += 1
        page = _truss_pages(pdf, res, page)
        page = _floor_pages(pdf, res, page)
        page = _issues_page(pdf, res, page)
        d = pdf.infodict()
        d["Title"] = f"{res.project} pranchas de framing"
        d["Author"] = "Vigora Frame Engine"
    return page - 1
