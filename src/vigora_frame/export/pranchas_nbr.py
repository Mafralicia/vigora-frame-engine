"""Pranchas de fabricação no padrão brasileiro (A1 ou A0) com legenda da Vigora.

Referências de formato e representação:
  NBR 10068 (folha de desenho: formatos, margens, legenda com 178 mm de largura),
  NBR 13142 (dobramento de cópias), NBR 8403 (tipos e larguras de linha),
  NBR 10126 (cotagem: traço oblíquo, texto sobre a linha de cota), NBR 8196 (escalas).

Tudo é desenhado num único eixo em milímetros do papel. Cada vista converte o modelo (mm)
para o papel com a escala exata, então 1:20 no carimbo é 1:20 na impressão em tamanho real.
"""
from __future__ import annotations

import datetime as _dt
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42      # TrueType embutida: texto legível e pesquisável em qualquer leitor
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon as MPoly, Rectangle  # noqa: E402

from ..model import Result  # noqa: E402
from .drawings import COLORS, LABEL  # noqa: E402

FORMATS = {"A1": (841.0, 594.0), "A0": (1189.0, 841.0)}
M_LEFT, M_OTHER = 25.0, 10.0          # NBR 10068
LEG_W = 178.0                         # largura da legenda (NBR 10068)
PT = 72 / 25.4                        # pontos por mm
BRAND = Path(__file__).resolve().parents[3] / "assets" / "brand"
INK = "#15110B"
INK2 = "#5A4C38"
LINE = "#2b2b2b"
PALETTE = {"wood": {"primary": "#8A5530", "accent": "#B8672F", "logo": "v-cobre.png", "soft": "#F2ECE3"},
           "steel": {"primary": "#414D57", "accent": "#3A73A0", "logo": "v-aco.png", "soft": "#E1E6EA"}}
ROLE_PT = {**LABEL, "STRINGER": "longarina", "TREAD": "piso do degrau", "HIP_RAFTER": "espigão", "TOP_CHORD": "banzo superior", "BOTTOM_CHORD": "banzo inferior", "WEB": "diagonal/montante",
           "GABLE_STUD": "montante de oitão", "JOIST": "viga de piso", "TAIL_JOIST": "viga curta", "TRIMMER": "viga lateral",
           "FLOOR_HEADER": "viga de borda do vão", "RIM": "viga de borda", "RIM_SIDE": "viga de borda lateral",
           "BRIDGING": "travamento", "CAP_PLATE": "placa de amarração"}
SCALES = [1, 2, 5, 10, 20, 25, 50, 75, 100, 125, 200]

_fonts_ok = False


def _fonts():
    global _fonts_ok
    if _fonts_ok:
        return
    for f in ("Archivo-Variable.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
        p = BRAND / f
        if p.exists():
            fm.fontManager.addfont(str(p))
    _fonts_ok = True


def _fam(kind):
    names = {f.name for f in fm.fontManager.ttflist}
    if kind == "mono":
        return "IBM Plex Mono" if "IBM Plex Mono" in names else "DejaVu Sans Mono"
    return "Archivo" if "Archivo" in names else "DejaVu Sans"


# ---------------------------------------------------------------- folha
class Sheet:
    def __init__(self, fmt: str, ctx: dict, number: int, total: int, title: str, subtitle: str, scale: str):
        _fonts()
        self._texts = []
        self.fmt = fmt
        self.W, self.H = FORMATS[fmt]
        self.ctx = ctx
        self.fig = plt.figure(figsize=(self.W / 25.4, self.H / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, self.W)
        self.ax.set_ylim(0, self.H)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.pal = PALETTE[ctx["system"]]
        self.number, self.total, self.title, self.subtitle, self.scale = number, total, title, subtitle, scale
        self._frame()
        self.leg_top = self._legend()
        self.right_x0 = self.W - M_OTHER - LEG_W
        # área de desenho: do quadro até a coluna da legenda
        self.area = (M_LEFT + 6, M_OTHER + 6, self.right_x0 - 6, self.H - M_OTHER - 6)
        self.col_top = self.H - M_OTHER - 4      # topo livre da coluna direita (acima da legenda)
        self.col_top_free = self.leg_top + 90

    # primitivas em mm de papel
    def text(self, x, y, s, h=2.5, kind="sans", weight="normal", ha="left", va="baseline", color=INK, rot=0,
             z=5, clip=None, mask=False, movable=False, anchor=None, rot_mode="default"):
        """Texto em mm de papel. mask: fundo branco (linhas não cortam o valor). movable: pode ser deslocado
        pela passada anticolisão (cotas e números de posição); anchor: ponto para a linha de chamada."""
        kw = {}
        if mask:
            kw["bbox"] = dict(boxstyle="square,pad=0.06", fc="white", ec="none")
        t = self.ax.text(x, y, s, fontsize=h * PT / 0.72, family=_fam(kind), weight=weight, ha=ha, va=va,
                         color=color, rotation=rot, zorder=z + (2 if mask else 0), rotation_mode=rot_mode, **kw)
        self._texts.append((t, movable, anchor or (x, y)))
        return t

    def line(self, pts, lw=0.25, color=LINE, ls="-", z=3):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, lw=lw * PT, color=color, ls=ls, zorder=z, solid_capstyle="butt")

    def rect(self, x, y, w, h, lw=0.25, ec=LINE, fc="none", z=2, hatch=None, alpha=1.0):
        self.ax.add_patch(Rectangle((x, y), w, h, lw=lw * PT, ec=ec, fc=fc, zorder=z, hatch=hatch, alpha=alpha))

    def poly(self, pts, lw=0.18, ec=LINE, fc="none", z=2, hatch=None, alpha=1.0, ls="-"):
        self.ax.add_patch(MPoly(pts, closed=True, lw=lw * PT, ec=ec, fc=fc, zorder=z, hatch=hatch, alpha=alpha, ls=ls))

    def image(self, path, x, y, w, h):
        import matplotlib.image as mpimg
        img = mpimg.imread(str(path))
        ih, iw = img.shape[:2]
        k = min(w / iw, h / ih)
        dw, dh = iw * k, ih * k
        self.ax.imshow(img, extent=(x + (w - dw) / 2, x + (w + dw) / 2, y + (h - dh) / 2, y + (h + dh) / 2), zorder=6)

    # cota alinhada NBR 10126: linha fina, traço oblíquo nas extremidades, texto sobre a linha
    def dim(self, p1, p2, off, text=None, h=2.0, ext=True, color=LINE, lift=0.0):
        (x1, y1), (x2, y2) = p1, p2
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 0.3:
            return
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        a = (x1 + nx * off, y1 + ny * off)
        b = (x2 + nx * off, y2 + ny * off)
        if ext:
            sgn = 1 if off >= 0 else -1
            for (px, py), (qx, qy) in (((x1, y1), a), ((x2, y2), b)):
                self.line([(px + nx * sgn * 1.0, py + ny * sgn * 1.0), (qx + nx * sgn * 1.5, qy + ny * sgn * 1.5)],
                          lw=0.13, color=color)
        self.line([(a[0] - ux * 1.2, a[1] - uy * 1.2), (b[0] + ux * 1.2, b[1] + uy * 1.2)], lw=0.13, color=color)
        for px, py in (a, b):   # traço oblíquo a 45°
            dx, dy = (ux + nx) * 1.1, (uy + ny) * 1.1
            self.line([(px - dx, py - dy), (px + dx, py + dy)], lw=0.3, color=color)
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90.1 or ang < -89.9:
            ang += 180
        mx, my = (a[0] + b[0]) / 2 + nx * (0.8 + lift), (a[1] + b[1]) / 2 + ny * (0.8 + lift)
        if lift:
            self.line([((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (mx - nx * 0.6, my - ny * 0.6)], lw=0.1, color=color)
        self.text(mx, my, text, h=h, ha="center", va="bottom", rot=ang, kind="mono", color=color, mask=True,
                  movable=True, anchor=((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))

    def chain(self, pts_paper, off, labels, h=1.8):
        """Cadeia de cotas. Valor que não cabe no trecho sobe uma fileira (alternando), sem colidir."""
        prev_short = False
        for (p, q), lab in zip(zip(pts_paper, pts_paper[1:]), labels):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            need = len(str(lab)) * h * 0.62 + 0.8
            short = L < need
            lift = (h * 1.35 if not prev_short else h * 2.7) if short else 0.0
            self.dim(p, q, off, lab, h=h, lift=lift)
            prev_short = short and not prev_short

    def view_title(self, x, y, num, title, scale_txt, w=None):
        """Título de vista no padrão: bolha com número + título sublinhado + escala."""
        r = 4.2
        self.ax.add_patch(Circle((x + r, y + r - 1.2), r, lw=0.35 * PT, ec=INK, fc="white", zorder=6))
        self.text(x + r, y + r - 1.2, str(num), h=3.0, ha="center", va="center", weight="bold", z=7)
        self.text(x + 2 * r + 2.5, y + 1.0, title, h=3.0, weight="bold", z=7)
        tl = w or (len(title) * 2.25 + 4)
        self.line([(x + 2 * r + 2.5, y - 0.2), (x + 2 * r + 2.5 + tl, y - 0.2)], lw=0.5, color=INK)
        self.text(x + 2 * r + 2.5, y - 4.0, scale_txt, h=2.1, kind="mono", color=INK2)

    def north(self, x, y, size=14, angle=0.0):
        s = size
        self.ax.add_patch(Circle((x, y), s / 2, lw=0.25 * PT, ec=INK, fc="none", zorder=6))
        pts = [(0, s / 2 * 0.95), (-s * 0.16, -s * 0.28), (0, -s * 0.12), (s * 0.16, -s * 0.28)]
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        P = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
        self.poly(P, lw=0.2, ec=INK, fc=self.pal["accent"], z=7)
        self.text(x, y + s / 2 + 1.5, "N", h=3.0, ha="center", weight="bold")

    def scale_bar(self, x, y, scale, meters=5):
        """Escala gráfica em metros."""
        L = 1000 / scale
        n = meters
        while n * L > 90 and n > 1:
            n -= 1
        for i in range(n):
            self.rect(x + i * L, y, L, 1.6, lw=0.2, ec=INK, fc=INK if i % 2 == 0 else "white", z=6)
            self.text(x + i * L, y + 2.4, f"{i}", h=1.7, ha="center", kind="mono")
        self.text(x + n * L, y + 2.4, f"{n} m", h=1.7, ha="center", kind="mono")

    def table(self, x, y_top, cols, rows, widths, h=1.9, row_h=3.4, header=True, max_rows=None, zebra=True):
        """Tabela simples; retorna y final."""
        y = y_top
        W = sum(widths)
        if header:
            self.rect(x, y - row_h, W, row_h, lw=0.25, ec=INK, fc=self.pal["soft"], z=4)
            cx = x
            for c, wdt in zip(cols, widths):
                self.text(cx + 1.0, y - row_h + 1.0, c, h=h * 0.95, weight="bold", z=6)
                cx += wdt
            y -= row_h
        for i, r in enumerate(rows[:max_rows] if max_rows else rows):
            if zebra and i % 2 == 1:
                self.rect(x, y - row_h, W, row_h, lw=0, ec="none", fc="#F6F3EE", z=3)
            cx = x
            for val, wdt in zip(r, widths):
                s = str(val)
                num = s.replace(".", "").replace(",", "").replace("-", "").replace("°", "").strip().isdigit()
                if num and wdt < 36:
                    self.text(cx + wdt - 1.0, y - row_h + 1.0, s, h=h, ha="right", kind="mono", z=6)
                else:
                    self.text(cx + 1.0, y - row_h + 1.0, s, h=h, z=6)
                cx += wdt
            y -= row_h
        self.rect(x, y, W, y_top - y, lw=0.3, ec=INK, z=5)
        cx = x
        for wdt in widths[:-1]:
            cx += wdt
            self.line([(cx, y), (cx, y_top)], lw=0.13, color="#888", z=5)
        return y

    # ---------------------------------------------------------- quadro, dobras e zonas
    def _frame(self):
        W, H = self.W, self.H
        self.rect(0, 0, W, H, lw=0.13, ec="#bbbbbb")                       # linha de corte
        self.rect(M_LEFT, M_OTHER, W - M_LEFT - M_OTHER, H - 2 * M_OTHER, lw=0.7, ec=INK)
        # zonas de referência (números no topo/base, letras nas laterais)
        nx = 8 if self.fmt == "A1" else 12
        ny = 6 if self.fmt == "A1" else 8
        x0, x1, y0, y1 = M_LEFT, W - M_OTHER, M_OTHER, H - M_OTHER
        for i in range(nx):
            xa = x0 + (x1 - x0) * i / nx
            if i:
                for yy in (y0, y1):
                    self.line([(xa, yy), (xa, yy + (4 if yy == y0 else -4))], lw=0.25, color=INK)
            for yy, off in ((y0, -3.8), (y1, 1.2)):
                self.text(xa + (x1 - x0) / nx / 2, yy + off, str(i + 1), h=2.0, ha="center", kind="mono", color=INK2)
        for j in range(ny):
            ya = y0 + (y1 - y0) * j / ny
            if j:
                for xx in (x0, x1):
                    self.line([(xx, ya), (xx + (4 if xx == x0 else -4), ya)], lw=0.25, color=INK)
            letter = "ABCDEFGHIJ"[ny - 1 - j]
            self.text(x0 - 3.5, ya + (y1 - y0) / ny / 2, letter, h=2.0, ha="center", va="center", kind="mono", color=INK2)
            self.text(x1 + 3.5, ya + (y1 - y0) / ny / 2, letter, h=2.0, ha="center", va="center", kind="mono", color=INK2)
        # marcas de dobra (NBR 13142): dobras verticais a cada 185 mm a partir da direita, horizontal a 297
        x = W - 185
        while x > 210:
            for yy in (0, H):
                self.line([(x, yy), (x, yy + (5 if yy == 0 else -5))], lw=0.2, color="#999")
            x -= 190
        for xx in (0, W):
            self.line([(xx, 297), (xx + (5 if xx == 0 else -5), 297)], lw=0.2, color="#999")
        # centragem
        for xx, yy, dx, dy in ((W / 2, 0, 0, 1), (W / 2, H, 0, -1), (0, H / 2, 1, 0), (W, H / 2, -1, 0)):
            self.line([(xx, yy), (xx + dx * 8, yy + dy * 8)], lw=0.5, color=INK)

    # ---------------------------------------------------------- legenda (carimbo) Vigora
    def _legend(self) -> float:
        c = self.ctx
        x0 = self.W - M_OTHER - LEG_W
        y = M_OTHER
        rows = [30, 17, 15, 19, 19, 24]
        Ht = sum(rows)
        top = y + Ht
        self.rect(x0, y, LEG_W, Ht, lw=0.7, ec=INK, fc="white", z=4)
        yy = top
        # 1) marca
        h = rows[0]
        yy -= h
        self.rect(x0, yy, 34, h, lw=0, fc=self.pal["soft"], z=4)
        logo = BRAND / self.pal["logo"]
        if logo.exists():
            self.image(logo, x0 + 4, yy + 3, 26, h - 6)
        self.text(x0 + 39, yy + h - 11.5, "VIGORA", h=8.0, weight="bold", z=6)
        self.text(x0 + 39, yy + h - 17.3, "WOOD FRAME · STEEL FRAME · ENGENHARIA", h=1.9, kind="mono",
                  color=self.pal["accent"], z=6)
        self.text(x0 + 39, yy + 4.2, "vigora.eng.br   ·   @grupovigora", h=2.0, kind="mono", color=INK2, z=6)
        self.text(x0 + LEG_W - 3, yy + h - 7, "Construção industrializada", h=1.9, ha="right", color=INK2, z=6)
        self.line([(x0, yy), (x0 + LEG_W, yy)], lw=0.5, color=INK, z=6)

        def field(xa, ya, wa, ha_, label, value, vh=2.6, bold=False, mono=False):
            self.line([(xa, ya), (xa + wa, ya)], lw=0.2, color=INK, z=6)
            self.text(xa + 1.2, ya + ha_ - 3.0, label, h=1.55, kind="mono", color=INK2, z=6)
            self.text(xa + 1.2, ya + 1.8, value, h=vh, weight="bold" if bold else "normal",
                      kind="mono" if mono else "sans", z=6)

        # 2) obra / cliente / local
        h = rows[1]
        yy -= h
        field(x0, yy, LEG_W, h, "OBRA / PROJETO", _cut(f"{c['project']} — {c['name']}", 62), vh=3.2, bold=True)
        self.text(x0 + LEG_W - 1.5, yy + h - 3.0, _cut(f"CLIENTE: {c['client']}   LOCAL: {c['site']}", 70), h=1.55,
                  kind="mono", color=INK2, ha="right", z=6)
        # 3) conteúdo da folha
        h = rows[2]
        yy -= h
        field(x0, yy, LEG_W, h, "CONTEÚDO DA FOLHA", _cut(self.title.upper(), 58), vh=3.0, bold=True)
        if self.subtitle:
            self.text(x0 + LEG_W - 1.5, yy + h - 3.0, _cut(self.subtitle, 60), h=1.55, kind="mono", color=INK2,
                      ha="right", z=6)
        # 4) dados técnicos: 4 colunas x 2 linhas
        h = rows[3]
        yy -= h
        cw = LEG_W / 4
        vals = [("DISCIPLINA", "ESTRUTURA / FRAMING"), ("SISTEMA", c["system_name"]), ("ESCALA", self.scale),
                ("FORMATO", f"{self.fmt} ({self.W:.0f}×{self.H:.0f})"),
                ("DATA", c["date"]), ("UNIDADE", "mm"), ("EXECUÇÃO", c["run"]), ("REVISÃO", c["rev"])]
        for i, (lab, val) in enumerate(vals):
            col, rowi = i % 4, i // 4
            xa, ya = x0 + col * cw, yy + (h / 2) * (1 - rowi)
            self.line([(xa, yy), (xa, yy + h)], lw=0.2, color=INK, z=6) if col else None
            self.text(xa + 1.2, ya + h / 2 - 2.8, lab, h=1.5, kind="mono", color=INK2, z=6)
            self.text(xa + 1.2, ya + 1.5, _cut(val, 20), h=2.1, kind="mono", z=6)
        self.line([(x0, yy + h / 2), (x0 + LEG_W, yy + h / 2)], lw=0.13, color="#999", z=6)
        self.line([(x0, yy + h), (x0 + LEG_W, yy + h)], lw=0.2, color=INK, z=6)
        # 5) responsáveis
        h = rows[4]
        yy -= h
        cw2 = [70, 38, 35, 35]
        vals = [("RESPONSÁVEL TÉCNICO", c["rt"]), ("CREA", c["crea"]), ("ART / RRT", c["art"]),
                ("DESENHO / VERIF.", c["drawn"])]
        xa = x0
        for (lab, val), wdt in zip(vals, cw2):
            if xa > x0:
                self.line([(xa, yy), (xa, yy + h)], lw=0.2, color=INK, z=6)
            self.text(xa + 1.2, yy + h - 3.0, lab, h=1.5, kind="mono", color=INK2, z=6)
            self.text(xa + 1.2, yy + 7.5, _cut(val, int(wdt / 1.9)), h=2.1, z=6)
            self.line([(xa + 2, yy + 3.5), (xa + wdt - 2, yy + 3.5)], lw=0.13, color="#999", z=6)
            xa += wdt
        self.line([(x0, yy + h), (x0 + LEG_W, yy + h)], lw=0.2, color=INK, z=6)
        # 6) status + folha + código
        h = rows[5]
        yy -= h
        approved = c["approved"]
        col = "#2E7D32" if approved else "#C62828"
        self.rect(x0 + 2, yy + 2, 92, h - 4, lw=0.5, ec=col, fc="white", z=6)
        self.text(x0 + 48, yy + h - 9.5, "APROVADO PARA FÁBRICA" if approved else "RASCUNHO", h=4.0 if not approved else 3.2,
                  weight="bold", ha="center", color=col, z=7)
        self.text(x0 + 48, yy + 5.0, "ruleset e catálogo aprovados" if approved else "NÃO LIBERADO PARA FÁBRICA",
                  h=1.8, kind="mono", ha="center", color=col, z=7)
        self.line([(x0 + 96, yy), (x0 + 96, yy + h)], lw=0.3, color=INK, z=6)
        self.text(x0 + 98, yy + h - 3.2, "FOLHA", h=1.5, kind="mono", color=INK2, z=6)
        self.text(x0 + 137, yy + 7.5, f"{self.number:02d}", h=9.0, weight="bold", ha="right", color=self.pal["primary"], z=6)
        self.text(x0 + 138, yy + 7.5, f"/{self.total:02d}", h=4.0, weight="bold", ha="left", color=INK2, z=6)
        self.text(x0 + 98, yy + 2.2, f"{c['project']}-FRM-{self.number:03d}-{c['rev']}", h=2.0, kind="mono", z=6)
        return top

    # ---------------------------------------------------------- coluna direita: revisões e notas
    def revisions_and_notes(self, notes: list[str]):
        x0 = self.right_x0
        y = self.leg_top + 2
        # quadro de revisões (preenchido de baixo para cima)
        rows = [[self.ctx["rev"], self.ctx["date"], "Emissão inicial (gerada pelo Vigora Frame Engine)", "VFE"]]
        rows += [["", "", "", ""]] * 3
        widths = [12, 22, 124, 20]
        h_tab = 3.4 * (len(rows) + 1)
        yb = y
        self.text(x0, yb + h_tab + 1.5, "QUADRO DE REVISÕES", h=2.0, weight="bold")
        ytop = yb + h_tab
        self.table(x0, ytop, ["REV.", "DATA", "DESCRIÇÃO", "POR"], list(reversed(rows)), widths, h=1.7, zebra=False)
        y = ytop + 7
        # notas gerais
        lines = []
        for i, n in enumerate(notes, 1):
            lines += _wrap(f"{i}. {n}", 92)
        h_notes = 4 + 3.0 * len(lines)
        self.rect(x0, y, LEG_W, h_notes, lw=0.3, ec=INK, fc="white", z=4)
        self.text(x0, y + h_notes + 1.5, "NOTAS GERAIS", h=2.0, weight="bold")
        yy = y + h_notes - 3.6
        for ln in lines:
            self.text(x0 + 1.5, yy, ln, h=1.75, z=6)
            yy -= 3.0
        self.col_top_free = y + h_notes + 6       # acima daqui fica livre para tabelas da folha
        return self.col_top_free

    def resolve_collisions(self):
        """Passada final: textos móveis (cotas, posições) que encostam em outro texto são deslocados."""
        r = self.fig.canvas.get_renderer()
        inv = self.ax.transData.inverted()

        def bb(t):
            e = t.get_window_extent(r)
            (x0, y0), (x1, y1) = inv.transform([(e.x0, e.y0), (e.x1, e.y1)])
            return [x0, y0, x1, y1]
        items = [(t, mv, anc, bb(t)) for t, mv, anc in self._texts if t.get_text().strip()]
        CELL = 20.0
        grid = {}

        def keys(b):
            for i in range(int(b[0] // CELL), int(b[2] // CELL) + 1):
                for j in range(int(b[1] // CELL), int(b[3] // CELL) + 1):
                    yield (i, j)

        def hits(b, pad=0.15):
            for kk in keys(b):
                for o in grid.get(kk, ()):
                    if b[0] < o[2] + pad and b[2] > o[0] - pad and b[1] < o[3] + pad and b[3] > o[1] - pad:
                        return True
            return False

        def add(b):
            for kk in keys(b):
                grid.setdefault(kk, []).append(b)
        moved = 0
        for t, mv, anc, b in sorted(items, key=lambda it: it[1]):      # fixos primeiro
            if not mv or not hits(b):
                add(b)
                continue
            w_, h_ = b[2] - b[0], b[3] - b[1]
            x, y = t.get_position()
            best = None
            for d in (1.2, 2.2, 3.4, 4.8, 6.5):
                for dx, dy in ((0, d), (0, -d), (d, 0), (-d, 0), (d, d), (-d, d), (d, -d), (-d, -d)):
                    nb = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy]
                    if not hits(nb):
                        best = (dx, dy, nb)
                        break
                if best:
                    break
            if best:
                dx, dy, nb = best
                t.set_position((x + dx, y + dy))
                cx, cy = (nb[0] + nb[2]) / 2, (nb[1] + nb[3]) / 2
                if abs(dx) + abs(dy) > 1.5:
                    self.ax.plot([anc[0], cx], [anc[1], cy], lw=0.08 * PT, color="#777", zorder=3)
                add(nb)
                moved += 1
            else:
                add(b)
        return moved

    def save(self, pdf):
        self.resolve_collisions()
        pdf.savefig(self.fig)
        plt.close(self.fig)


def _cut(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _wrap(s, n):
    words, out, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = "    " + w
        else:
            cur = (cur + " " + w).strip() if not cur.startswith("    ") or cur.strip() else cur + w
    if cur:
        out.append(cur)
    return out


def _fit_scale(model_w, model_h, box_w, box_h, allowed=(20, 25, 50, 75, 100, 125, 200)):
    for s in allowed:
        if model_w / s <= box_w and model_h / s <= box_h:
            return s
    return allowed[-1]


# ---------------------------------------------------------------- geometria auxiliar
def _panel_band(pn, x0=None, x1=None):
    from ..revit_bridge import _clip_poly
    return _clip_poly(pn, 0.0 if x0 is None else x0, pn.length if x1 is None else x1, pn.depth or 140.0)


class View:
    def __init__(self, sheet: Sheet, x, y, scale, mx, my):
        self.s, self.x, self.y, self.k, self.mx, self.my = sheet, x, y, 1.0 / scale, mx, my

    def P(self, X, Y):
        return (self.x + (X - self.mx) * self.k, self.y + (Y - self.my) * self.k)


# ---------------------------------------------------------------- folhas
def _notes(res: Result, ctx) -> list[str]:
    n = [
        "Medidas em milímetros, exceto onde indicado. Não medir no desenho: usar as cotas.",
        f"Sistema {ctx['system_name']}; regras {res.ruleset}; peças conforme catálogo (código na lista de materiais).",
        "Comprimentos de corte já descontam folgas; ângulos de corte indicados em relação ao esquadro.",
        "Painéis montados na mesa de fabricação na ordem das posições; conferir esquadro por diagonais (dif. ≤ 3 mm).",
        "Juntas das placas sempre sobre montante, verga, bloqueio ou placa; pregação/parafusamento conforme norma do fabricante.",
        "Nenhum vão entre peças maior que 2,5 mm e menor que 60 mm: peças encostadas ou com vão livre (verificação V-074).",
        "Folhas geradas automaticamente pelo Vigora Frame Engine a partir do modelo. Alterações somente no modelo.",
    ]
    if not res.ruleset_approved:
        n.append("RASCUNHO: regras e catálogo sem aprovação do engenheiro responsável. Não liberar para corte.")
    return n


def _cover(sh: Sheet, res: Result, q: dict, index: list):
    x0, y0, x1, y1 = sh.area
    c = sh.ctx
    sh.text(x0 + 2, y1 - 16, "PROJETO DE FRAMING", h=4.0, kind="mono", color=sh.pal["accent"])
    sh.text(x0 + 2, y1 - 32, _cut(c["name"], 48), h=11.0, weight="bold")
    sh.text(x0 + 2, y1 - 42, f"{c['project']}  ·  {c['system_name']}  ·  {res.stats['panels']} painéis  ·  "
                             f"{res.stats['members']} peças  ·  {res.stats['trusses']} treliças", h=3.2, color=INK2)
    sh.line([(x0 + 2, y1 - 47), (x0 + 120, y1 - 47)], lw=1.2, color=sh.pal["accent"])
    # render 3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from ..revit_bridge import revit_solids
    bw, bh = (x1 - x0) * 0.62, (y1 - y0) - 70
    ax3 = sh.fig.add_axes([(x0) / sh.W, (y0 + 4) / sh.H, bw / sh.W, bh / sh.H], projection="3d")
    faces, cols = [], []
    for s in revit_solids(res)["solids"]:
        p, e = s["profile"], s["extrude"]
        qq = [[a[0] + e[0], a[1] + e[1], a[2] + e[2]] for a in p]
        faces += [p, qq] + [[p[i], p[(i + 1) % len(p)], qq[(i + 1) % len(p)], qq[i]] for i in range(len(p))]
        cols += [COLORS.get(s["role"], "#ccc")] * (2 + len(p))
    if faces:
        ax3.add_collection3d(Poly3DCollection(faces, facecolors=cols, edgecolors="#5d4037", linewidths=0.04))
        xs = [v[0] for f in faces for v in f]
        ys = [v[1] for f in faces for v in f]
        zs = [v[2] for f in faces for v in f]
        ax3.set_xlim(min(xs), max(xs))
        ax3.set_ylim(min(ys), max(ys))
        ax3.set_zlim(min(zs), max(zs))
        ax3.set_box_aspect((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    ax3.view_init(elev=24, azim=-58)
    ax3.set_axis_off()
    # índice de folhas
    xi = x0 + bw + 8
    yi = y1 - 58
    sh.text(xi, yi + 6, "ÍNDICE DE FOLHAS", h=2.6, weight="bold")
    rows = [[f"{n:02d}", t] for n, t in index]
    yi = sh.table(xi, yi + 3, ["FL.", "CONTEÚDO"], rows, [12, (x1 - xi) - 14], h=1.9, row_h=3.5)
    # resumo quantitativo
    st, sm = res.stats, q["summary"]
    rows = [["Painéis", f"{st['panels']} ({st['unique_panels']} diferentes)"],
            ["Peças lineares", f"{st['members']}"], ["Metros lineares", f"{sm['linear_m']:.1f} m"],
            ["Barras a comprar", f"{sm['bars']} (aproveit. {sm['yield'] * 100:.1f}%)"],
            ["Placas a comprar", f"{sm['sheets']}"], ["Peso das peças lineares", f"{sm['kg_linear']:.0f} kg"],
            ["Treliças", f"{st['trusses']} em {len(res.trusses)} marcas"],
            ["Erros / avisos", f"{st['issues'].get('error', 0)} / {st['issues'].get('warning', 0)}"]]
    sh.text(xi, yi - 8, "RESUMO", h=2.6, weight="bold")
    sh.table(xi, yi - 11, ["ITEM", "VALOR"], rows, [42, (x1 - xi) - 44], h=1.9, row_h=3.5, header=False)


def _plan_levels(res: Result):
    lv = defaultdict(list)
    for pn in res.panels:
        lv[pn.level].append(pn)
    return lv


def _plan_sheet(sh: Sheet, res: Result, level: str, panels: list, vnum: int):
    from shapely.geometry import MultiPolygon
    from shapely.ops import unary_union
    x0, y0, x1, y1 = sh.area
    bands = [(pn, _panel_band(pn)) for pn in panels]
    allp = unary_union([b for _, b in bands])
    minx, miny, maxx, maxy = allp.bounds
    scale = _fit_scale(maxx - minx + 3000, maxy - miny + 3000, x1 - x0 - 30, y1 - y0 - 40, (50, 75, 100, 125, 200))
    k = 1 / scale
    pw = (maxx - minx) * k
    left_free = 102.0 if (x1 - x0 - pw) / 2 > 110 else 0.0         # espaço do quadro de painéis
    cx = x0 + left_free + (x1 - x0 - left_free - pw) / 2
    cy = y0 + 22 + (y1 - y0 - 40 - (maxy - miny) * k) / 2
    V = View(sh, cx, cy, scale, minx, miny)
    centroid = allp.centroid
    # paredes (faixa preenchida), juntas de painel, aberturas
    for pn, band in bands:
        polys = [band] if band.geom_type == "Polygon" else list(band.geoms)
        for pg in polys:
            pts = [V.P(x, y) for x, y in pg.exterior.coords]
            sh.poly(pts, lw=0.5, ec=INK, fc=sh.pal["soft"] if pn.exterior else "#EFEFEF", z=3)
        d = pn.direction
        nrm = (-d[1], d[0])
        dep = pn.depth or 140
        for op in pn.openings:
            a, b = op["x0"], op["x1"]
            gap = _panel_band(pn, a, b)
            sh.poly([V.P(x, y) for x, y in gap.exterior.coords], lw=0.0, ec="white", fc="white", z=4)
            A = (pn.origin[0] + d[0] * a, pn.origin[1] + d[1] * a)
            B = (pn.origin[0] + d[0] * b, pn.origin[1] + d[1] * b)
            for kk in (-0.5, 0.5):
                sh.line([V.P(A[0] + nrm[0] * dep * kk, A[1] + nrm[1] * dep * kk),
                         V.P(B[0] + nrm[0] * dep * kk, B[1] + nrm[1] * dep * kk)], lw=0.25, color=INK, z=5)
            if op["door"]:
                # folha de porta aberta a 90° com arco (lado interno)
                mid = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
                side = 1 if (centroid.x - mid[0]) * nrm[0] + (centroid.y - mid[1]) * nrm[1] > 0 else -1
                wdt = b - a
                H0 = (A[0] + nrm[0] * side * dep / 2, A[1] + nrm[1] * side * dep / 2)
                leaf = (H0[0] + nrm[0] * side * wdt, H0[1] + nrm[1] * side * wdt)
                sh.line([V.P(*H0), V.P(*leaf)], lw=0.35, color=INK, z=5)
                a0 = math.degrees(math.atan2(d[1], d[0]))
                a1 = math.degrees(math.atan2(nrm[1] * side, nrm[0] * side))
                t1, t2 = sorted([a0, a1])
                if t2 - t1 > 180:
                    t1, t2 = t2, t1 + 360
                pc = V.P(*H0)
                sh.ax.add_patch(Arc(pc, 2 * wdt * V.k, 2 * wdt * V.k, theta1=t1, theta2=t2, lw=0.18 * PT, color=INK,
                                    ls=(0, (4, 2)), zorder=5))
            else:
                sh.line([V.P(A[0], A[1]), V.P(B[0], B[1])], lw=0.18, color=INK, z=5)
        # juntas de painel e etiqueta
        for u in (0.0, pn.length):
            P0 = (pn.origin[0] + d[0] * u + nrm[0] * dep / 2, pn.origin[1] + d[1] * u + nrm[1] * dep / 2)
            P1 = (pn.origin[0] + d[0] * u - nrm[0] * dep / 2, pn.origin[1] + d[1] * u - nrm[1] * dep / 2)
            sh.line([V.P(*P0), V.P(*P1)], lw=0.35, color=sh.pal["accent"], z=6)
        mid = (pn.origin[0] + d[0] * pn.length / 2, pn.origin[1] + d[1] * pn.length / 2)
        side = -1 if (centroid.x - mid[0]) * nrm[0] + (centroid.y - mid[1]) * nrm[1] > 0 else 1
        off = (dep / 2 + 5.5 / V.k) * (1 if pn.exterior else 0.0) + (0 if pn.exterior else dep / 2 + 3.2 / V.k)
        tp = V.P(mid[0] + nrm[0] * side * off, mid[1] + nrm[1] * side * off)
        tag = f"{pn.wall}-{pn.id.split('-PN')[-1]}"
        wtag = len(tag) * 1.45 + 3
        sh.rect(tp[0] - wtag / 2, tp[1] - 1.9, wtag, 3.8, lw=0.25, ec=sh.pal["primary"], fc="white", z=7)
        sh.text(tp[0], tp[1], tag, h=1.9, ha="center", va="center", kind="mono", color=sh.pal["primary"], z=8)
    # cotas gerais externas
    pts_x = sorted({round(V.P(x, miny)[0], 2) for pn, b in bands if pn.exterior for x in (b.bounds[0], b.bounds[2])
                    if abs(b.bounds[1] - miny) < 5})
    if len(pts_x) >= 2:
        yb = V.P(0, miny)[1]
        pp = [(x, yb) for x in pts_x]
        sh.chain(pp, -10, [f"{(q[0] - p[0]) / V.k:.0f}" for p, q in zip(pp, pp[1:])])
    sh.dim(V.P(minx, miny), V.P(maxx, miny), -17, f"{maxx - minx:.0f}", h=2.2)
    sh.dim(V.P(minx, maxy), V.P(minx, miny), -17, f"{maxy - miny:.0f}", h=2.2)
    pts_y = sorted({round(V.P(minx, y)[1], 2) for pn, b in bands if pn.exterior for y in (b.bounds[1], b.bounds[3])
                    if abs(b.bounds[0] - minx) < 5})
    if len(pts_y) >= 2:
        xb = V.P(minx, 0)[0]
        pp = [(xb, y) for y in reversed(pts_y)]
        sh.chain(pp, -10, [f"{(p[1] - q[1]) / V.k:.0f}" for p, q in zip(pp, pp[1:])])
    sh.north(x1 - 14, y1 - 16)
    # quadro de painéis do pavimento (canto superior esquerdo da área)
    rows = [[f"{pn.wall}-{pn.id.split('-PN')[-1]}", pn.wall_type, f"{pn.length:.0f}", f"{pn.height:.0f}",
             f"{pn.weight_kg:.0f}", "sim" if pn.special else ""] for pn in sorted(panels, key=lambda p: p.id)]
    tw = [22, 14, 16, 14, 12, 12]
    room = int((y1 - y0 - 30) / 3.0) - 1
    if left_free:
        sh.text(x0 + 2, y1 - 4, "QUADRO DE PAINÉIS", h=2.0, weight="bold")
        sh.table(x0 + 2, y1 - 6, ["PAINEL", "TIPO", "COMPR.", "ALT.", "kg", "ESP."], rows, tw, h=1.6, row_h=3.0,
                 max_rows=room)
    sh.view_title(x0 + 2, y0 + 8, vnum, f"PLANTA DE PAINÉIS — {level}", f"ESC. 1:{scale}   ·   corte a 1,20 m do piso")
    sh.scale_bar(x0 + 130, y0 + 6, scale)
    return scale


def _roof_sheet(sh: Sheet, res: Result, vnum: int):
    x0, y0, x1, y1 = sh.area
    tr_ids = sorted({m.parent for m in res.members if m.frame == "truss"})
    if not tr_ids:
        return None
    segs = []
    for tid in tr_ids:
        pl = res.stats["placements"].get(tid)
        if not pl:
            continue
        ms = [m for m in res.members if m.parent == tid]
        span = max(m.x1 for m in ms)
        start = min(m.x0 for m in ms)
        o, sd = pl["origin"], pl["span_dir"]
        mark = next((m.note.split()[1].rstrip(";") for m in ms if m.note.startswith("marca")), "?")
        plies = max(m.plies for m in ms)
        segs.append((tid, (o[0] + sd[0] * start, o[1] + sd[1] * start), (o[0] + sd[0] * span, o[1] + sd[1] * span),
                     mark, plies, sd))
    xs = [p[0] for s in segs for p in (s[1], s[2])]
    ys = [p[1] for s in segs for p in (s[1], s[2])]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    tab_w = 0
    scale = _fit_scale(maxx - minx + 3000, maxy - miny + 3000, x1 - x0 - 30 - tab_w, y1 - y0 - 45, (50, 75, 100, 125, 200))
    V = View(sh, x0 + 20 + (x1 - x0 - 30 - (maxx - minx) / scale) / 2, y0 + 24 + (y1 - y0 - 45 - (maxy - miny) / scale) / 2,
             scale, minx, miny)
    # paredes em cinza claro por baixo
    for pn in res.panels:
        if pn.level != max(p.level for p in res.panels):
            continue
        b = _panel_band(pn)
        if b.geom_type == "Polygon":
            sh.poly([V.P(x, y) for x, y in b.exterior.coords], lw=0.15, ec="#999", fc="#EEEEEE", z=2)
    colors = {"T": sh.pal["primary"], "G": "#6D4C41", "D": "#C77D2E", "M": "#8E2A1C", "J": sh.pal["accent"],
              "V": "#1f6fb2", "A": "#2F6FA8"}
    _roof_lines(sh, res, V)
    for t in res.stats.get("tanks", []):          # caixa d'água em projeção: bacia tracejada + caixa + capacidade
        c = V.P(*t["center"])
        sh.ax.add_patch(Circle(c, t["R_tray"] * V.k, lw=0.3 * PT, ec="#2F6FA8", fc="none", ls=(0, (4, 2)), zorder=8))
        sh.ax.add_patch(Circle(c, t["tank_d"] / 2 * V.k, lw=0.45 * PT, ec="#2F6FA8", fc="#D6E6F4", alpha=0.85, zorder=8))
        sh.text(c[0], c[1] + 1.0, f"CX {t['capacity']} L", h=2.0, ha="center", weight="bold", color="#1b4f7a", z=9,
                mask=True)
        sh.text(c[0], c[1] - 2.6, "ático · bacia Ø" + f"{t['R_tray'] * 2:.0f}", h=1.5, ha="center", kind="mono",
                color="#1b4f7a", z=9, mask=True)
    for tid, a, b, mark, plies, sd in segs:
        th = 38 * plies * V.k
        A, B = V.P(*a), V.P(*b)
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
        nx, ny = -uy * th / 2, ux * th / 2
        sh.poly([(A[0] + nx, A[1] + ny), (B[0] + nx, B[1] + ny), (B[0] - nx, B[1] - ny), (A[0] - nx, A[1] - ny)],
                lw=0.2, ec=INK, fc=colors.get(mark[0], "#999"), z=4)
        tp = (A[0] + ux * min(6, L / 3), A[1] + uy * min(6, L / 3))
        sh.text(tp[0] - uy * 2.2, tp[1] + ux * 2.2, mark, h=1.7, kind="mono", ha="center", va="center",
                rot=math.degrees(math.atan2(uy, ux)), z=6)
    # cota de espaçamento ao longo da cumeeira (treliças paralelas: usa a coordenada perpendicular ao vão)
    main = [s for s in segs if s[3][0] in "TGDMA"]
    if main:
        sd = main[0][5]
        if abs(sd[1]) > 0.5:
            pos = sorted({round(s[1][0], 1) for s in main})
            yb = V.P(0, miny)[1]
            pp = [(V.P(p, 0)[0], yb) for p in pos]
            sh.chain(pp, -8, [f"{q - p:.0f}" for p, q in zip(pos, pos[1:])], h=1.6)
        else:
            pos = sorted({round(s[1][1], 1) for s in main})
            xb = V.P(minx, 0)[0]
            pp = [(xb, V.P(0, p)[1]) for p in reversed(pos)]
            sh.chain(pp, -8, [f"{p - q:.0f}" for p, q in zip(reversed(pos), list(reversed(pos))[1:])], h=1.6)
    sh.north(x1 - 14, y1 - 16)
    sh.view_title(x0 + 2, y0 + 8, vnum, "PLANTA DE COBERTURA — TRELIÇAS", f"ESC. 1:{scale}   ·   marcas conforme detalhamento")
    sh.scale_bar(x0 + 130, y0 + 6, scale)
    return scale


def _roof_lines(sh: Sheet, res: Result, V):
    """Projeção do telhado: beiral (tracejado), cumeeira, espigões e rincões (traço-ponto), com nomes."""
    roofs = res.stats.get("roofs", [])

    def g(ra, al, sp_):          # (ao longo, vão) -> planta
        return (al, sp_) if ra == "x" else (sp_, al)
    for r in roofs:
        ra, o_al, Lr, o_sp, S, ov = r["ridge_axis"], r["o_along"], r["Lr"], r["o_span"], r["span"], r["ovh"]
        rake = 0.0 if r.get("support") == "parapet" else ov
        e0 = rake if r["ends"][0] == "gable" else 0.0
        e1 = rake if r["ends"][1] == "gable" else 0.0
        box = [g(ra, o_al - e0, o_sp - ov), g(ra, o_al + Lr + e1, o_sp - ov), g(ra, o_al + Lr + e1, o_sp + S + ov),
               g(ra, o_al - e0, o_sp + S + ov)]
        sh.poly([V.P(*q) for q in box], lw=0.25, ec="#555", fc="none", ls=(0, (6, 3)), z=6)
        mid = o_sp + S / 2
        if r["kind"] == "gable":
            a0, a1 = o_al - e0, o_al + Lr + e1
            for vi, e_ in enumerate(r["ends"]):
                if e_ == "valley":
                    # a cumeeira da asa avança sobre o principal até encontrar o plano dele
                    main = next((m for m in roofs if m["id"] != r["id"] and m["level"] == r["level"]
                                 and m["ridge_axis"] != ra), None)
                    if main:
                        u_r = (r["ridge_z"] - main["z_top"] - main["T0"]) / main["tan"] if main["tan"] else 0
                        face = o_al if vi == 0 else o_al + Lr
                        dv = -1 if vi == 0 else 1
                        tip = face + dv * max(0.0, u_r)
                        if vi == 0:
                            a0 = tip
                        else:
                            a1 = tip
                        for sp_ in (o_sp, o_sp + S):          # rincões: dos cantos da asa até a ponta da cumeeira
                            p0, p1 = V.P(*g(ra, face, sp_)), V.P(*g(ra, tip, mid))
                            sh.line([p0, p1], lw=0.35, color="#1f6fb2", ls=(0, (8, 2, 2, 2)), z=7)
                        mp = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                        sh.text(mp[0] + 1.5, mp[1], "RINCÃO", h=1.8, kind="mono", color="#1f6fb2", z=8, mask=True,
                                movable=True)
            p0, p1 = V.P(*g(ra, a0, mid)), V.P(*g(ra, a1, mid))
            sh.line([p0, p1], lw=0.45, color=INK, ls=(0, (8, 2, 2, 2)), z=7)
            sh.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 1.2, "CUMEEIRA", h=1.8, kind="mono", ha="center",
                    z=8, mask=True, movable=True, rot=0 if ra == "x" else 90)
        elif r["kind"] == "hip":
            half = S / 2
            a0, a1 = o_al + half, o_al + Lr - half
            p0, p1 = V.P(*g(ra, a0, mid)), V.P(*g(ra, a1, mid))
            sh.line([p0, p1], lw=0.45, color=INK, ls=(0, (8, 2, 2, 2)), z=7)
            sh.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 1.2, "CUMEEIRA", h=1.8, kind="mono", ha="center",
                    z=8, mask=True, movable=True, rot=0 if ra == "x" else 90)
            for al, sp_, apex in ((o_al, o_sp, a0), (o_al, o_sp + S, a0), (o_al + Lr, o_sp, a1),
                                  (o_al + Lr, o_sp + S, a1)):
                sh.line([V.P(*g(ra, al, sp_)), V.P(*g(ra, apex, mid))], lw=0.35, color="#8E2A1C",
                        ls=(0, (8, 2, 2, 2)), z=7)
            q0, q1 = V.P(*g(ra, o_al, o_sp)), V.P(*g(ra, a0, mid))
            sh.text((q0[0] + q1[0]) / 2 + 1.5, (q0[1] + q1[1]) / 2, "ESPIGÃO", h=1.8, kind="mono", color="#8E2A1C",
                    z=8, mask=True, movable=True)
        # seta de caimento em cada água
        for sp_, sgn in (((o_sp + S * 0.25), -1), ((o_sp + S * 0.75), 1)) if r["kind"] != "mono" else \
                (((o_sp + S * 0.5), 1 if r.get("flip") else -1),):
            c_ = V.P(*g(ra, o_al + Lr * 0.5, sp_))
            dvec = (0, sgn) if ra == "x" else (sgn, 0)
            tip_ = (c_[0] + dvec[0] * 7, c_[1] + dvec[1] * 7)
            sh.line([c_, tip_], lw=0.3, color=INK2, z=7)
            sh.poly([tip_, (tip_[0] - dvec[0] * 2 + dvec[1] * 1, tip_[1] - dvec[1] * 2 + dvec[0] * 1),
                     (tip_[0] - dvec[0] * 2 - dvec[1] * 1, tip_[1] - dvec[1] * 2 - dvec[0] * 1)], lw=0, ec="none",
                    fc=INK2, z=7)
            sh.text(c_[0] + (2 if ra == "x" else 0), c_[1] + (0 if ra == "x" else 2), f"{math.tan(math.radians(r['pitch'])) * 100:.0f}%",
                    h=1.7, kind="mono", z=8, mask=True, movable=True)


def _roof_table(sh: Sheet, res: Result):
    x0 = sh.right_x0
    ytop = sh.H - M_OTHER - 10
    sh.text(x0, ytop + 2, "QUADRO DE TRELIÇAS", h=2.0, weight="bold")
    rows = [[t.mark, t.type, f"{t.span:.0f}", f"{t.height:.0f}", f"{t.pitch_deg:g}°", t.count] for t in res.trusses]
    return sh.table(x0, ytop, ["MARCA", "TIPO", "VÃO", "ALTURA", "INCL.", "QTD"], rows, [16, 62, 24, 24, 20, 32], h=1.8)


def _bevel(m):
    import re
    r_ = re.search(r"(?:chanfro de|chanfrado a) ([\d.]+)°", m.note or "")
    return float(r_.group(1)) if r_ else None


def _positions(ms):
    """Agrupa peças iguais (função, item, comprimento, ângulos, chanfro) em posições numeradas."""
    key = lambda m: (m.role, m.item, round(m.cut_length), m.angle_a, m.angle_b, _bevel(m))
    groups = defaultdict(list)
    for m in ms:
        groups[key(m)].append(m)
    order = sorted(groups, key=lambda k: (-(k[2]), k[0]))
    pos = {}
    for i, kk in enumerate(order, 1):
        for m in groups[kk]:
            pos[m.id] = i
    return pos, [(i, kk, len(groups[kk])) for i, kk in enumerate(order, 1)]


def _panel_cell(sh: Sheet, res: Result, pn, x, y, w, h, scale, vnum, sheets_by_panel):
    k = 1 / scale
    ms = [m for m in res.members if m.parent == pn.id and m.frame == "panel"]
    core = [m for m in ms if m.plane == "core"]
    pos, table = _positions(core)
    H = pn.height
    # bloco = desenho + cotas + título + lista; centralizado na célula
    ncol_ = 2 if len(table) > 9 else 1
    per_ = math.ceil(len(table) / ncol_)
    tw_ = [6, 27, 24, 12, 11, 7]
    tab_w = ncol_ * (sum(tw_) + 3)
    tab_h = (per_ + 1) * 2.55
    left_pad, top_pad, below = 22.0, 8.0, 44.0
    bw = max(left_pad + pn.length * k + 4, tab_w + 2)
    bh = top_pad + H * k + below + tab_h
    bx = x + max(0.0, (w - bw) / 2)
    by_top = y + h - max(0.0, (h - bh) / 2)
    ox = bx + left_pad
    oy = by_top - top_pad - H * k
    x = bx - 2                                 # a lista e o título se alinham ao bloco
    V = View(sh, ox, oy, scale, 0, 0)
    # placas (tracejado azul) por trás
    for s in sheets_by_panel.get(pn.id, []):
        sh.rect(ox + s.x0 * k, oy + s.z0 * k, (s.x1 - s.x0) * k, (s.z1 - s.z0) * k, lw=0.18, ec="#3A73A0", fc="none",
                z=2)
    for op in pn.openings:
        sh.rect(ox + op["x0"] * k, oy + op["z0"] * k, (op["x1"] - op["x0"]) * k, (op["z1"] - op["z0"]) * k,
                lw=0.25, ec="#7a7a7a", fc="none", z=2)
        cx_, cz_ = ox + (op["x0"] + op["x1"]) / 2 * k, oy + (op["z0"] + op["z1"]) / 2 * k
        sh.line([(ox + op["x0"] * k, oy + op["z0"] * k), (ox + op["x1"] * k, oy + op["z1"] * k)], lw=0.13, color="#aaa")
        sh.line([(ox + op["x0"] * k, oy + op["z1"] * k), (ox + op["x1"] * k, oy + op["z0"] * k)], lw=0.13, color="#aaa")
        sh.text(cx_, cz_, f"{op['id']}\n{op['x1'] - op['x0']:.0f}×{op['z1'] - op['z0']:.0f}", h=1.6, ha="center",
                va="center", kind="mono", color=INK2, z=6)
    for m in ms:
        if m.plane != "core":
            continue
        fc = COLORS.get(m.role, "#ddd")
        if m.polygon:
            sh.poly([(ox + px * k, oy + pz * k) for px, pz in m.polygon], lw=0.13, ec=INK, fc=fc, z=3)
        else:
            sh.rect(ox + m.x0 * k, oy + m.z0 * k, (m.x1 - m.x0) * k, (m.z1 - m.z0) * k, lw=0.13, ec=INK, fc=fc, z=3)
    # peças chanfradas (meia-esquadria): hachura + etiqueta com o ângulo
    for m in core:
        bv = _bevel(m)
        if bv is None:
            continue
        sh.rect(ox + m.x0 * k, oy + m.z0 * k, (m.x1 - m.x0) * k, (m.z1 - m.z0) * k, lw=0.3, ec="#8E2A1C",
                fc="none", hatch="\\\\\\", z=4)
        cxm = ox + (m.x0 + m.x1) / 2 * k
        top_ = oy + H * k
        sh.poly([(cxm, top_ + 1.2), (cxm - 1.3, top_ + 3.4), (cxm + 1.3, top_ + 3.4)], lw=0, ec="none", fc="#8E2A1C", z=6)
        lab = f"CH {bv:g}°" + (" pilarete CNC" if "pilarete" in (m.note or "") else "")
        sh.text(cxm, top_ + 4.2, lab, h=1.5, ha="center", kind="mono", color="#8E2A1C", z=6)
    # números de posição (uma etiqueta por peça grande; peças pequenas só se couber)
    for m in core:
        wpx, hpx = (m.x1 - m.x0) * k, (m.z1 - m.z0) * k
        if max(wpx, hpx) < 3.5:
            continue
        cxm, czm = ox + (m.x0 + m.x1) / 2 * k, oy + (m.z0 + m.z1) / 2 * k
        rot = 90 if hpx > wpx else 0
        sh.text(cxm, czm, str(pos[m.id]), h=1.25, ha="center", va="center", kind="mono", rot=rot, z=6, mask=True,
                movable=True, anchor=(cxm, czm))
    # cotas acumuladas (NBR 10126, cotagem por coordenadas) até a face esquerda de cada peça vertical;
    # valores próximos vão para uma segunda/terceira fileira (nenhum valor é omitido)
    xs_ = sorted({round(m.x0, 1) for m in core if m.orientation == "V"} | {0.0, round(pn.length, 1)})
    last = [-1e9, -1e9, -1e9]
    for v in xs_:
        px = ox + v * k
        tier = next((i for i, lp in enumerate(last) if px - lp >= 2.3), 2)
        last[tier] = px
        yl = oy - 3.8 - tier * 5.2
        sh.line([(px, oy - 0.8), (px, yl + 0.4)], lw=0.1 if tier else 0.13)
        sh.text(px, yl, f"{v:.0f}", h=1.25, ha="center", va="top", rot=90, kind="mono", mask=True)
    sh.line([(ox, oy - 2.1), (ox + pn.length * k, oy - 2.1)], lw=0.13)
    sh.dim((ox, oy), (ox + pn.length * k, oy), -21, f"{pn.length:.0f}", h=1.9)
    zs = sorted({0.0, round(H, 1)} | {round(m.z1, 1) for m in core if m.role == "BOTTOM_PLATE"} |
                {round(m.z0, 1) for m in core if m.role == "TOP_PLATE"} |
                {round(v, 1) for op in pn.openings for v in (op["z0"], op["z1"]) if 0 < v < H})
    last = [-1e9, -1e9, -1e9]
    for v in zs:
        pz = oy + v * k
        tier = next((i for i, lp in enumerate(last) if pz - lp >= 2.3), 2)
        last[tier] = pz
        xl = ox - 3.8 - tier * 6.0
        sh.line([(ox - 0.8, pz), (xl + 0.4, pz)], lw=0.1 if tier else 0.13)
        sh.text(xl, pz, f"{v:.0f}", h=1.25, ha="right", va="center", kind="mono", mask=True)
    sh.line([(ox - 2.1, oy), (ox - 2.1, oy + H * k)], lw=0.13)
    # título da vista
    wt = pn.id.split(f"{res.project}-")[-1]
    sh.view_title(x + 2, oy - 31, vnum, f"PAINEL {pn.wall}-{pn.id.split('-PN')[-1]}",
                  f"ESC. 1:{scale}  ·  {pn.length:.0f} × {H:.0f}  ·  {pn.weight_kg:.0f} kg  ·  {wt}"
                  + ("  ·  ESPECIAL" if pn.special else "") + "  ·  cotas acumuladas até a face esquerda", w=60)
    # lista de posições (até 3 colunas)
    rows = []
    for i, kk, n in table:
        role, item, L, a1, a2, bv = kk
        ang = "" if (a1 in (90, None) and a2 in (90, None)) else f"{a1:g}/{a2:g}°"
        if bv:
            ang = f"ch {bv:g}°"
        rows.append([i, _cut(ROLE_PT.get(role, role.lower()), 18), item, f"{L}", ang, n])
    ncol = 2 if len(rows) > 9 else 1
    per = math.ceil(len(rows) / ncol)
    tw = [6, 27, 24, 12, 11, 7]
    for c in range(ncol):
        sub = rows[c * per:(c + 1) * per]
        if sub:
            sh.table(x + 2 + c * (sum(tw) + 3), oy - 40, ["P", "FUNÇÃO", "ITEM", "CORTE", "ÂNG.", "QT"], sub, tw,
                     h=1.35, row_h=2.55)


def _truss_cell(sh: Sheet, res: Result, mark, x, y, w, h, scale, vnum):
    k = 1 / scale
    ms = [m for m in res.members if m.id in set(mark.member_ids)]
    if not ms:
        return
    minx = min(m.x0 for m in ms)
    maxx = max(m.x1 for m in ms)
    maxz = max(m.z1 for m in ms)
    ox = x + 8 - minx * k
    oy = y + h - 6 - maxz * k
    for m in ms:
        sh.poly([(ox + px * k, oy + pz * k) for px, pz in m.polygon], lw=0.15, ec=INK, fc=COLORS.get(m.role, "#ddd"), z=3)
    pos, table = _positions(ms)
    for m in ms:
        cxm = ox + (m.x0 + m.x1) / 2 * k
        czm = oy + (m.z0 + m.z1) / 2 * k
        sh.text(cxm, czm, str(pos[m.id]), h=1.3, ha="center", va="center", kind="mono", z=6)
    bot = [m for m in ms if m.role == "BOTTOM_CHORD"]
    b0, b1 = min(m.x0 for m in bot), max(m.x1 for m in bot)
    sh.dim((ox + b0 * k, oy), (ox + b1 * k, oy), -5, f"vão {mark.span:.0f}", h=1.7)
    sh.dim((ox + minx * k, oy), (ox + maxx * k, oy), -10, f"{maxx - minx:.0f}", h=1.7)
    sh.dim((ox + maxx * k, oy), (ox + maxx * k, oy + maxz * k), -4, f"{maxz:.0f}", h=1.7)
    sh.view_title(x + 2, oy - 22, vnum, f"TRELIÇA {mark.mark} — {mark.type.upper()}",
                  f"ESC. 1:{scale}  ·  {mark.count} un.  ·  incl. {mark.pitch_deg:g}°", w=58)
    rows = []
    for i, kk, n in table:
        role, item, L, a1, a2, _bv = kk
        rows.append([i, _cut(ROLE_PT.get(role, role.lower()), 18), item, f"{L}", f"{a1:g}/{a2:g}°" if a1 else "", n])
    tw = [6, 27, 26, 12, 13, 7]
    per = math.ceil(len(rows) / 2) if len(rows) > 8 else len(rows)
    for c in range(2 if len(rows) > 8 else 1):
        sub = rows[c * per:(c + 1) * per]
        sh.table(x + 2 + c * (sum(tw) + 3), oy - 31, ["P", "FUNÇÃO", "ITEM", "CORTE", "ÂNG.", "QT"], sub, tw,
                 h=1.35, row_h=2.55)


def _details(res: Result):
    """Encontros típicos (L, T, X, meia-esquadria) encontrados no próprio projeto."""
    from shapely.ops import unary_union
    bands = {}
    for pn in res.panels:
        bands.setdefault((pn.level, pn.wall), []).append(_panel_band(pn))
    walls = {k: unary_union(v) for k, v in bands.items()}
    out, seen = [], set()
    keys = sorted(walls)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a[0] != b[0]:
                continue
            if walls[a].distance(walls[b]) > 0.6:
                continue
            inter = walls[a].buffer(0.8).intersection(walls[b].buffer(0.8))
            if inter.is_empty:
                continue
            p = inter.centroid
            pa = [pn for pn in res.panels if pn.level == a[0] and pn.wall == a[1]]
            pb = [pn for pn in res.panels if pn.level == b[0] and pn.wall == b[1]]
            da, db = pa[0].direction, pb[0].direction
            ang = abs(math.degrees(math.acos(max(-1, min(1, abs(da[0] * db[0] + da[1] * db[1]))))))
            clip = any(pn.clip_start or pn.clip_end for pn in pa + pb)
            if clip:
                kind = "MEIA-ESQUADRIA" if ang > 20 else "FACETA"
            elif ang < 5:
                continue
            else:
                near_end = lambda pns: any(math.hypot(p.x - (pn.origin[0] + pn.direction[0] * u),
                                                      p.y - (pn.origin[1] + pn.direction[1] * u)) < 400
                                           for pn in pns for u in (0, pn.length))
                ea, eb = near_end(pa), near_end(pb)
                kind = "CANTO L" if ea and eb else "ENCONTRO T"
                if a[1].endswith(("A", "B")) or b[1].endswith(("A", "B")):
                    kind = "CRUZAMENTO X" if kind == "ENCONTRO T" else kind
            ext = any(pn.exterior for pn in pa + pb) and kind not in ("CRUZAMENTO X", "MEIA-ESQUADRIA", "FACETA")
            key = (kind, ext)
            if key in seen:
                continue
            seen.add(key)
            out.append((kind + (" (externa)" if ext and kind != "CRUZAMENTO X" else ""), a, b, (p.x, p.y), a[0]))
    order = {"CANTO L": 0, "ENCONTRO T": 1, "CRUZAMENTO X": 2, "MEIA-ESQUADRIA": 3, "FACETA": 4}
    out.sort(key=lambda t: (order.get(t[0].split(" (")[0], 9), "(externa)" not in t[0]))
    first, rest, kinds = [], [], set()
    for d in out:                       # um de cada tipo primeiro, depois as variações
        k_ = d[0].split(" (")[0]
        (rest if k_ in kinds else first).append(d)
        kinds.add(k_)
    return (first + rest)[:6]


def _detail_cell(sh: Sheet, res: Result, det, solids, x, y, w, h, vnum):
    from shapely.geometry import MultiPoint, Point, box
    kind, a, b, (px, py), level = det
    R = min(550.0, (min(w - 55, h - 45)) * 10 / 2)
    scale = 10
    k = 1 / scale
    # enquadramento pelo conteúdo: as paredes do encontro ficam no centro da célula
    from shapely.ops import unary_union
    bnd = unary_union([_panel_band(pn) for pn in res.panels if pn.level == level and pn.wall in (a[1], b[1])])
    cont = bnd.intersection(box(px - 1.6 * R, py - 1.6 * R, px + 1.6 * R, py + 1.6 * R))
    if cont.is_empty:
        cxw, cyw, half = px, py, R
    else:
        bx0, by0, bx1, by1 = cont.bounds
        cxw, cyw = (bx0 + bx1) / 2, (by0 + by1) / 2
        half = min(R, max(bx1 - bx0, by1 - by0) / 2 + 160)
        cxw = min(max(cxw, px - half + 200), px + half - 200)
        cyw = min(max(cyw, py - half + 200), py + half - 200)
    R = half
    win = box(cxw - R, cyw - R, cxw + R, cyw + R)
    ox, oy = x + (w - 50) / 2, y + h / 2 + 12
    V = View(sh, ox, oy, scale, cxw, cyw)
    lv_elev = next((lv["elevation"] for lv in sh.ctx["levels"] if lv["id"] == level), 0.0)
    # altura de corte livre de peças horizontais (bloqueio, verga, peitoril) perto do encontro
    horiz = [(s_["profile"], s_["extrude"]) for s_ in solids if s_["group"] == "wall" and
             s_["role"] in ("BLOCK", "HEADER", "SILL", "PACKER", "STRAP")]
    zc = lv_elev + 1200
    for zt in (1200, 1100, 1300, 1000, 1400, 900, 1500, 800):
        z_ = lv_elev + zt
        hit = False
        for prof, ex in horiz:
            p3 = prof + [[v[0] + ex[0], v[1] + ex[1], v[2] + ex[2]] for v in prof]
            if min(v[2] for v in p3) - 5 <= z_ <= max(v[2] for v in p3) + 5 and \
                    MultiPoint([(v[0], v[1]) for v in p3]).convex_hull.intersects(win):
                hit = True
                break
        if not hit:
            zc = z_
            break
    pan = {pn.id: pn for pn in res.panels}
    # faixa das paredes (fundo claro, faces tracejadas) e cota da espessura
    for pn in res.panels:
        if pn.level != level or pn.wall not in (a[1], b[1]):
            continue
        band = _panel_band(pn).intersection(win)
        if band.is_empty or band.geom_type != "Polygon":
            continue
        sh.poly([V.P(xx, yy) for xx, yy in band.exterior.coords], lw=0.18, ec="#8a8a8a", fc="#F4F1EC", z=1, ls="--")
    labeled = {}
    cuts = []
    drawn = 0
    for s in solids:
        if s["group"] != "wall":
            continue
        pn = pan.get(s["parent"])
        if not pn or pn.level != level:
            continue
        p3 = s["profile"] + [[v[0] + s["extrude"][0], v[1] + s["extrude"][1], v[2] + s["extrude"][2]] for v in s["profile"]]
        z0, z1 = min(v[2] for v in p3), max(v[2] for v in p3)
        if not (z0 <= zc <= z1):
            continue
        hull = MultiPoint([(v[0], v[1]) for v in p3]).convex_hull
        if hull.geom_type != "Polygon" or not hull.intersects(win):
            continue
        cut = hull.intersection(win)
        if cut.is_empty or cut.geom_type != "Polygon":
            continue
        role = s["role"]
        sh.poly([V.P(xx, yy) for xx, yy in cut.exterior.coords], lw=0.35, ec=INK, fc=COLORS.get(role, "#ddd"),
                hatch="////" if res.system == "wood" else None, z=3)
        drawn += 1
        cuts.append((cut, s["parent"]))
        c_ = cut.centroid
        if role not in labeled or c_.distance(win.centroid) < labeled[role][0]:
            labeled[role] = (c_.distance(win.centroid), (c_.x, c_.y))
    # placa externa (OSB/cimentícia) na face externa das paredes externas
    for pn in res.panels:
        if pn.level != level or not pn.exterior or pn.wall not in (a[1], b[1]):
            continue
        d = pn.direction
        nrm = (-d[1], d[0])
        dep = pn.depth or 140
        cen = (sum(p.origin[0] for p in res.panels) / len(res.panels), sum(p.origin[1] for p in res.panels) / len(res.panels))
        mid = (pn.origin[0] + d[0] * pn.length / 2, pn.origin[1] + d[1] * pn.length / 2)
        side = -1 if (cen[0] - mid[0]) * nrm[0] + (cen[1] - mid[1]) * nrm[1] > 0 else 1
        from shapely.geometry import Polygon as SP
        t = 11.1
        o = pn.origin
        q = [(o[0] + nrm[0] * side * dep / 2, o[1] + nrm[1] * side * dep / 2)]
        q.append((q[0][0] + d[0] * pn.length, q[0][1] + d[1] * pn.length))
        q.append((q[1][0] + nrm[0] * side * t, q[1][1] + nrm[1] * side * t))
        q.append((q[0][0] + nrm[0] * side * t, q[0][1] + nrm[1] * side * t))
        c = SP(q).intersection(win)
        if not c.is_empty and c.geom_type == "Polygon":
            sh.poly([V.P(xx, yy) for xx, yy in c.exterior.coords], lw=0.25, ec="#3A73A0", fc="#D6E4F0", z=3)
    # números em bolha (um por tipo de peça, na peça mais próxima do encontro) + legenda ao lado, sem linhas
    roles = sorted(labeled, key=lambda r_: -labeled[r_][1][1])
    for i_, role in enumerate(roles, 1):
        cxm, cym = labeled[role][1]
        pp = V.P(cxm, cym)
        sh.ax.add_patch(Circle(pp, 1.7, lw=0.25 * PT, ec=INK, fc="white", zorder=8))
        sh.text(pp[0], pp[1], str(i_), h=1.5, ha="center", va="center", weight="bold", z=9)
    lx, ly = ox + R * k + 4, oy + R * k - 3
    for i_, role in enumerate(roles, 1):
        sh.ax.add_patch(Circle((lx + 1.7, ly + 0.6), 1.7, lw=0.25 * PT, ec=INK, fc="white", zorder=8))
        sh.text(lx + 1.7, ly + 0.6, str(i_), h=1.5, ha="center", va="center", weight="bold", z=9)
        sh.text(lx + 5, ly, ROLE_PT.get(role, role.lower()), h=1.7, z=6)
        ly -= 4.4
    # cotas face a face ao longo de cada parede (folgas reais), do lado de fora da faixa
    for wid_ in (a[1], b[1]):
        pns = [pn for pn in res.panels if pn.level == level and pn.wall == wid_]
        if not pns:
            continue
        pn0 = min(pns, key=lambda p_: Point(p_.origin[0], p_.origin[1]).distance(Point(px, py)))
        d_ = pn0.direction
        nrm = (-d_[1], d_[0])
        dep_ = pn0.depth or 140
        ivs = []
        for poly_, pid_ in cuts:
            pn_ = pan.get(pid_)
            if pn_ is None or pn_.wall != wid_:
                continue
            t_ax0 = (px - pn0.origin[0]) * d_[0] + (py - pn0.origin[1]) * d_[1]
            ax0 = (pn0.origin[0] + d_[0] * t_ax0, pn0.origin[1] + d_[1] * t_ax0)
            us = [(xx - ax0[0]) * d_[0] + (yy - ax0[1]) * d_[1] for xx, yy in poly_.exterior.coords]
            ivs.append((min(us), max(us)))
        if not ivs:
            continue
        faces = sorted({round(v, 1) for iv in ivs for v in iv})
        if len(faces) < 2:
            continue
        cen = (sum(p_.origin[0] for p_ in res.panels) / len(res.panels), sum(p_.origin[1] for p_ in res.panels) / len(res.panels))
        side = -1 if (cen[0] - px) * nrm[0] + (cen[1] - py) * nrm[1] > 0 else 1
        # linha de referência: face externa da parede, a partir do EIXO da parede (projeção do encontro no eixo)
        t_ax = (px - pn0.origin[0]) * d_[0] + (py - pn0.origin[1]) * d_[1]
        c0 = (pn0.origin[0] + d_[0] * t_ax, pn0.origin[1] + d_[1] * t_ax)
        off_face = side * (dep_ / 2 + (12 if pn0.exterior else 0))
        pts = [V.P(c0[0] + d_[0] * u_ + nrm[0] * off_face, c0[1] + d_[1] * u_ + nrm[1] * off_face) for u_ in faces]
        # a cota vai para fora da parede: normal da linha de cota no mesmo sentido do lado externo
        ux_, uy_ = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
        sgn = 1 if (-uy_) * (nrm[0] * side) + ux_ * (nrm[1] * side) > 0 else -1
        sh.chain(pts, sgn * 4, [f"{q_ - p_:.0f}" for p_, q_ in zip(faces, faces[1:])], h=1.4)
    # espessuras, fora do quadro
    yl = oy - R * k - 16
    for pn in res.panels:
        if pn.level == level and pn.wall in (a[1], b[1]):
            pass
    thick = []
    for wid_ in (a[1], b[1]):
        pn_ = next((p_ for p_ in res.panels if p_.level == level and p_.wall == wid_), None)
        if pn_:
            thick.append(f"{wid_}: {pn_.depth or 140:.0f} mm")
    sh.text(ox - R * k, yl, "espessura do quadro — " + "  ·  ".join(thick), h=1.6, kind="mono", color=INK2)
    sh.rect(ox - R * k, oy - R * k, 2 * R * k, 2 * R * k, lw=0.18, ec="#999", fc="none", z=2)
    sh.text(ox - R * k, oy + R * k + 1.5, f"{a[1]} × {b[1]}", h=1.8, kind="mono", color=INK2)
    sh.view_title(ox - R * k, oy - R * k - 26, vnum, f"DETALHE — {kind}",
                  f"ESC. 1:10  ·  corte horizontal a {(zc - lv_elev) / 1000:.2f} m  ·  peças cortadas hachuradas", w=62)
    return drawn


def _fixings(sh: Sheet, rules):
    """Quadro de fixações das ligações (das regras do projeto) na coluna direita."""
    def spec(fid):
        import re
        m_ = re.search(r"(\d+(?:\.\d+)?)x(\d+)", fid)
        kind = "prego anelado" if fid.startswith("PREGO") else ("parafuso autobrocante" if "AUTOBROC" in fid else
                                                                 ("parafuso de placa" if "PARAF" in fid else fid.lower()))
        return f"{kind} Ø{m_.group(1)} × {m_.group(2)} mm" if m_ else kind
    rows = []
    for code, c in rules.data.get("connections", {}).items():
        if c.get("qty_per_m"):
            q_ = f"a cada {1000 / c['qty_per_m']:.0f} mm (alternado)"
        elif c.get("qty"):
            q_ = f"{c['qty']} por ligação"
        else:
            continue
        if "nó" in c["name"] or "viga" in c["name"]:
            continue
        rows.append([code, _cut(c["name"], 24), _cut(spec(c["fastener"]), 32), q_])
    fs = rules.data.get("sheathing", {}).get("fastening")
    if fs:
        rows.append(["PL", "placa estrutural", _cut(spec(fs["fastener"]), 32),
                     f"borda {fs['edge_pitch']} / campo {fs['field_pitch']} mm"])
    an = rules.data.get("anchorage", {}).get("base")
    if an:
        rows.append(["AN", "painel-fundação", spec(an["item"]).replace("chumbador-m12", "chumbador M12"),
                     f"a cada {an['pitch']} mm; ≤ {an['max_from_plate_end']} mm da ponta"])
    y = sh.col_top_free + 4 + 3.1 * (len(rows) + 1)
    sh.text(sh.right_x0, y + 2, "QUADRO DE FIXAÇÕES (valores das regras do projeto)", h=2.0, weight="bold")
    sh.table(sh.right_x0, y, ["LIG.", "LIGAÇÃO", "FIXADOR", "QUANTIDADE / PASSO"], rows, [12, 44, 58, 64], h=1.55,
             row_h=3.1)


def _bom_sheet(sh: Sheet, res: Result, q: dict):
    x0, y0, x1, y1 = sh.area
    colw = (x1 - x0 - 10) / 2
    rows = [[c["item"], c["pieces"], f"{c['cut_m']:.1f}", c["bars_total"], f"{c['yield'] * 100:.0f}%", f"{c['kg']:.0f}"]
            for c in q["consolidated"]]
    sh.text(x0, y1 - 4, "PEÇAS LINEARES (PLANO DE CORTE OTIMIZADO)", h=2.6, weight="bold")
    yb = sh.table(x0, y1 - 7, ["ITEM", "PEÇAS", "CORTE (m)", "BARRAS", "APROV.", "kg"], rows,
                  [46, 18, 24, 20, 18, 20], h=1.9, row_h=3.6)
    rows = [[s["item"], s["positions"], f"{s['net_m2']:.1f}", s["sheets_to_buy"]] for s in q["sheets"]]
    sh.text(x0, yb - 10, "PLACAS", h=2.6, weight="bold")
    yb = sh.table(x0, yb - 13, ["ITEM", "POSIÇÕES", "ÁREA LÍQ. (m²)", "COMPRAR"], rows, [54, 24, 34, 24], h=1.9, row_h=3.6)
    rows = [[h_["item"], h_["unit"], h_["qty"], h_["qty_buy"]] for h_ in q["hardware"]]
    xr = x0 + colw + 10
    sh.text(xr, y1 - 4, "FERRAGENS E FIXAÇÕES", h=2.6, weight="bold")
    yr = sh.table(xr, y1 - 7, ["ITEM", "UN.", "QTD", "COMPRAR (+perda)"], rows, [60, 14, 22, 34], h=1.9, row_h=3.6)
    rows = [[p["id"].split(f"{res.project}-")[-1], p["type"], f"{p['length']:.0f}", f"{p['height']:.0f}",
             f"{p['weight_kg']:.0f}", p["members"], p["signature"][:6]] for p in q["panels"]]
    sh.text(xr, yr - 10, "PAINÉIS (ORDEM DE FABRICAÇÃO)", h=2.6, weight="bold")
    maxr = int((yr - 13 - y0) / 3.1) - 1
    sh.table(xr, yr - 13, ["PAINEL", "TIPO", "COMPR.", "ALT.", "kg", "PEÇAS", "ASSIN."], rows, [42, 16, 18, 14, 14, 16, 18],
             h=1.7, row_h=3.1, max_rows=maxr)
    if len(rows) > maxr:
        sh.text(xr, y0 + 2, f"(+{len(rows) - maxr} painéis na planilha quantitativo.xlsx)", h=1.8, color=INK2)


def _issues_sheet(sh: Sheet, res: Result):
    x0, y0, x1, y1 = sh.area
    st = res.stats["issues"]
    sh.text(x0, y1 - 6, "RELATÓRIO DE VALIDAÇÃO", h=4.0, weight="bold")
    sh.text(x0, y1 - 13, f"{st.get('error', 0)} erros · {st.get('warning', 0)} avisos · {st.get('info', 0)} informações · "
                         "todas as verificações do modelo (V-001 a V-081)", h=2.4, color=INK2)
    rows = [[i.severity.upper(), i.code, _cut(i.element, 26), _cut(i.message, 118)]
            for i in sorted(res.issues, key=lambda i: {"error": 0, "warning": 1, "info": 2}[i.severity])]
    maxr = int((y1 - 22 - y0) / 3.3) - 1
    sh.table(x0, y1 - 18, ["NÍVEL", "CÓDIGO", "ELEMENTO", "MENSAGEM"], rows, [18, 16, 50, x1 - x0 - 86], h=1.8,
             row_h=3.3, max_rows=maxr)


# ---------------------------------------------------------------- montagem
def write_pranchas(res: Result, q: dict, path: str, fmt: str = "A1", levels: list | None = None) -> int:
    from ..config import Rules
    from ..revit_bridge import revit_solids
    rules = Rules.load("wood-br-v1" if res.system == "wood" else "steel-br-v1")
    meta = res.meta or {}
    ctx = {"project": res.project, "name": res.project_name, "system": res.system,
           "system_name": "WOOD FRAME" if res.system == "wood" else "STEEL FRAME (LSF)",
           "client": meta.get("cliente", "—"), "site": meta.get("local", "—"),
           "rt": meta.get("responsavel_tecnico", "Eng.º ________________"), "crea": meta.get("crea", "________"),
           "art": meta.get("art", "________"), "drawn": meta.get("desenho", "VFE / ______"),
           "date": meta.get("data", _dt.date.today().strftime("%d/%m/%Y")), "rev": meta.get("revisao", "R00"),
           "run": res.run_id[:10], "approved": res.ruleset_approved, "levels": levels or []}
    W, Hh = FORMATS[fmt]
    area_w = W - M_LEFT - M_OTHER - LEG_W - 12 - 12
    area_h = Hh - 2 * M_OTHER - 12
    plan_lv = _plan_levels(res)
    sheets_by_panel = defaultdict(list)
    for s in res.sheets:
        sheets_by_panel[s.parent].append(s)
    # distribuição das elevações: grade que cabe na área a 1:20 (ou 1:25)
    ncols = 2 if fmt == "A1" else 3
    nrows = 2
    cell_w, cell_h = area_w / ncols, area_h / nrows
    panels = sorted(res.panels, key=lambda p: (p.level, p.wall, p.id))
    per = ncols * nrows
    panel_pages = [panels[i:i + per] for i in range(0, len(panels), per)]
    marks = sorted(res.trusses, key=lambda t: t.mark)

    def tsize(t):
        ms = [m for m in res.members if m.id in set(t.member_ids)]
        wd = (max(m.x1 for m in ms) - min(m.x0 for m in ms)) / 25 + 22 if ms else 100
        ntab = len({(m.role, m.item, round(m.cut_length)) for m in ms})
        return max(wd, 97 if ntab <= 8 else 194), t.height / 25 + 40 + 2.6 * min(ntab, math.ceil(ntab / 2) if ntab > 8 else ntab)

    # empacotamento em linhas: várias treliças por linha quando couberem
    truss_pages, page, row, row_w, row_h, used = [], [], [], 0.0, 0.0, 0.0
    for t in marks:
        w_, h_ = tsize(t)
        if row and row_w + w_ > area_w:
            page.append((row, row_h))
            used += row_h
            row, row_w, row_h = [], 0.0, 0.0
        if page and used + max(row_h, h_) > area_h:
            truss_pages.append(page)
            page, used = [], 0.0
        row.append((t, w_, h_))
        row_w += w_
        row_h = max(row_h, h_)
    if row:
        page.append((row, row_h))
    if page:
        truss_pages.append(page)
    dets = _details(res)
    floors = sorted({m.parent for m in res.members if m.group == "floor"})
    plan = [("capa", None, "Capa, índice e resumo")]
    for lv in sorted(plan_lv):
        plan.append(("planta", lv, f"Planta de painéis — {lv}"))
    if res.trusses:
        plan.append(("cobertura", None, "Planta de cobertura"))
    for f in floors:
        plan.append(("piso", f, f"Entrepiso {f.split('-')[-1]}"))
    for i, pg in enumerate(panel_pages):
        plan.append(("paineis", pg, f"Elevações de painéis {pg[0].wall}…{pg[-1].wall}"))
    for i, pg in enumerate(truss_pages):
        plan.append(("trelicas", pg, "Treliças " + ", ".join(t.mark for row, _ in pg for t, _, _ in row)))
    for st in res.stats.get("stairs", []):
        plan.append(("escada", st, f"Escada {st['id'].split('-')[-1]} — planta e corte"))
    if dets:
        plan.append(("detalhes", dets, "Detalhes típicos dos encontros"))
    plan.append(("materiais", None, "Lista de materiais"))
    plan.append(("validacao", None, "Relatório de validação"))
    total = len(plan)
    index = [(i + 1, t) for i, (_, _, t) in enumerate(plan)]
    solids = revit_solids(res)["solids"]
    notes = _notes(res, ctx)
    vnum = 0
    with PdfPages(path) as pdf:
        for n, (kind, data, title) in enumerate(plan, 1):
            scale_txt = "INDICADA"
            if kind == "capa":
                sh = Sheet(fmt, ctx, n, total, "Capa, índice e resumo", "", "SEM ESCALA")
                sh.revisions_and_notes(notes)
                _cover(sh, res, q, index)
            elif kind == "planta":
                sh = Sheet(fmt, ctx, n, total, title, "paredes, painéis, aberturas e cotas gerais", "")
                vnum += 1
                s_ = _plan_sheet(sh, res, data, plan_lv[data], vnum)
                sh.scale = f"1:{s_}"
                sh.revisions_and_notes(notes)
                _legend_fix(sh)
            elif kind == "cobertura":
                sh = Sheet(fmt, ctx, n, total, title, "posição e marca das treliças", "")
                vnum += 1
                s_ = _roof_sheet(sh, res, vnum)
                sh.scale = f"1:{s_}"
                sh.revisions_and_notes(notes)
                _roof_table(sh, res)
                _legend_fix(sh)
            elif kind == "piso":
                sh = Sheet(fmt, ctx, n, total, title, "vigas, bordas e aberturas do piso", "")
                vnum += 1
                sh.revisions_and_notes(notes)
                s_ = _floor_sheet(sh, res, data, vnum)
                sh.scale = f"1:{s_}"
                _legend_fix(sh)
            elif kind == "paineis":
                maxL = max(p.length for p in data)
                sc = 20 if maxL <= (cell_w - 26) * 20 and max(p.height for p in data) / 20 <= cell_h - 75 else 25
                sh = Sheet(fmt, ctx, n, total, title, f"{len(data)} painéis · posições numeradas", f"1:{sc}")
                sh.revisions_and_notes(notes)
                _roles_legend(sh)
                x0, y0, x1, y1 = sh.area
                for i, pn in enumerate(data):
                    r_, c_ = divmod(i, ncols)
                    vnum += 1
                    _panel_cell(sh, res, pn, x0 + c_ * cell_w, y1 - (r_ + 1) * cell_h, cell_w, cell_h, sc, vnum,
                                sheets_by_panel)
            elif kind == "trelicas":
                sh = Sheet(fmt, ctx, n, total, title, "geometria, peças e ângulos de corte", "1:25")
                sh.revisions_and_notes(notes)
                x0, y0, x1, y1 = sh.area
                tot_h = sum(rh for _, rh in data)
                yy = y1 - max(0.0, (y1 - y0 - tot_h) / 2)
                for row, rh in data:
                    row_w = sum(w_ for _, w_, _ in row)
                    xx = x0 + max(0.0, (x1 - x0 - row_w) / 2)
                    for t, w_, h_ in row:
                        vnum += 1
                        _truss_cell(sh, res, t, xx, yy - rh, w_, rh, 25, vnum)
                        xx += w_
                    yy -= rh
            elif kind == "detalhes":
                sh = Sheet(fmt, ctx, n, total, title, "cortes horizontais gerados do modelo", "1:10")
                sh.revisions_and_notes(notes)
                _fixings(sh, rules)
                x0, y0, x1, y1 = sh.area
                nc = 3
                cw, ch = (x1 - x0) / nc, (y1 - y0) / 2
                nrow = math.ceil(len(data) / nc)
                ytop = y1 - (2 - nrow) * ch / 2                       # grade centralizada na vertical
                for i, d in enumerate(data):
                    r_, c_ = divmod(i, nc)
                    in_row = min(nc, len(data) - r_ * nc)
                    xoff = (nc - in_row) * cw / 2                     # linha incompleta centralizada
                    vnum += 1
                    _detail_cell(sh, res, d, solids, x0 + xoff + c_ * cw, ytop - (r_ + 1) * ch, cw, ch, vnum)
            elif kind == "escada":
                sh = Sheet(fmt, ctx, n, total, title, "planta, corte A-A e peças", "1:25")
                sh.revisions_and_notes(notes)
                holes = [h_ for f_ in res.stats.get("floor_holes", []) for h_ in f_]
                vnum += 1
                _stair_sheet(sh, res, data, vnum, holes)
                vnum += 1
            elif kind == "materiais":
                sh = Sheet(fmt, ctx, n, total, title, "consolidado do projeto", "SEM ESCALA")
                sh.revisions_and_notes(notes)
                _bom_sheet(sh, res, q)
            else:
                sh = Sheet(fmt, ctx, n, total, title, "verificações automáticas", "SEM ESCALA")
                sh.revisions_and_notes(notes)
                _issues_sheet(sh, res)
            sh.save(pdf)
    return total


def _legend_fix(sh: Sheet):
    """Reescreve o campo de escala da legenda depois que a vista escolheu a escala."""
    x0 = sh.W - M_OTHER - LEG_W
    rows = [30, 17, 15, 19, 19, 24]
    y_dados = M_OTHER + rows[5] + rows[4]
    cw = LEG_W / 4
    xa, ya = x0 + 2 * cw, y_dados + rows[3] / 2
    sh.rect(xa + 0.4, ya + 0.4, cw - 0.8, rows[3] / 2 - 3.6, lw=0, ec="none", fc="white", z=7)
    sh.text(xa + 1.2, ya + 1.5, sh.scale, h=2.1, kind="mono", z=8)


def _roles_legend(sh: Sheet):
    y = sh.col_top_free + 2
    x0 = sh.right_x0
    items = [(r, ROLE_PT.get(r, r)) for r in ("STUD", "STUD_END", "KING", "JACK", "HEADER", "SILL", "CRIPPLE", "BACKER",
                                                "BLOCK", "BOTTOM_PLATE", "TOP_PLATE", "NAILER", "PACKER")]
    sh.text(x0, y + 4 + 3.2 * math.ceil(len(items) / 2), "LEGENDA DAS PEÇAS", h=2.0, weight="bold")
    for i, (r, lab) in enumerate(items):
        c, rr = divmod(i, math.ceil(len(items) / 2))
        xx = x0 + c * 89
        yy = y + 3.2 * (math.ceil(len(items) / 2) - rr)
        sh.rect(xx, yy - 0.6, 6, 2.4, lw=0.13, ec=INK, fc=COLORS.get(r, "#ddd"), z=5)
        sh.text(xx + 8, yy, lab, h=1.7, z=6)
    sh.line([(x0, y - 1), (x0 + 12, y - 1)], lw=0.18, color="#3A73A0")
    sh.text(x0 + 14, y - 1.6, "contorno das placas estruturais", h=1.7)


def _floor_sheet(sh: Sheet, res: Result, fid: str, vnum: int):
    x0, y0, x1, y1 = sh.area
    ms = [m for m in res.members if m.parent == fid]
    minx = min(m.x0 for m in ms)
    maxx = max(m.x1 for m in ms)
    miny = min(m.z0 for m in ms)
    maxy = max(m.z1 for m in ms)
    scale = _fit_scale(maxx - minx + 2500, maxy - miny + 2500, x1 - x0 - 30, y1 - y0 - 45, (25, 50, 75, 100, 125))
    V = View(sh, x0 + 20 + (x1 - x0 - 30 - (maxx - minx) / scale) / 2, y0 + 26 + (y1 - y0 - 45 - (maxy - miny) / scale) / 2,
             scale, minx, miny)
    for s in res.sheets:
        if s.parent == fid:
            a, b = V.P(s.x0, s.z0), V.P(s.x1, s.z1)
            sh.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], lw=0.15, ec="#3A73A0", fc="none", z=2)
    pos, table = _positions(ms)
    for m in ms:
        a, b = V.P(m.x0, m.z0), V.P(m.x1, m.z1)
        sh.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], lw=0.15, ec=INK, fc=COLORS.get(m.role, "#ddd"), z=3)
        if max(b[0] - a[0], b[1] - a[1]) > 12:
            sh.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, str(pos[m.id]), h=1.3, ha="center", va="center", kind="mono",
                    rot=90 if (b[1] - a[1]) > (b[0] - a[0]) else 0, z=6)
    js = [m for m in ms if m.role in ("JOIST",)]
    if js:
        along_y = (js[0].z1 - js[0].z0) > (js[0].x1 - js[0].x0)
        if along_y:
            cs = sorted({round((m.x0 + m.x1) / 2, 1) for m in js})
            pp = [V.P(c, miny) for c in cs]
            sh.chain(pp, -8, [f"{b - a:.0f}" for a, b in zip(cs, cs[1:])], h=1.5)
        else:
            cs = sorted({round((m.z0 + m.z1) / 2, 1) for m in js})
            pp = [V.P(minx, c) for c in reversed(cs)]
            sh.chain(pp, -8, [f"{a - b:.0f}" for a, b in zip(reversed(cs), list(reversed(cs))[1:])], h=1.5)
    sh.dim(V.P(minx, miny), V.P(maxx, miny), -15, f"{maxx - minx:.0f}", h=2.2)
    sh.dim(V.P(minx, maxy), V.P(minx, miny), -15, f"{maxy - miny:.0f}", h=2.2)
    sh.north(x1 - 14, y1 - 16)
    sh.view_title(x0 + 2, y0 + 8, vnum, f"ENTREPISO {fid.split('-')[-1]}", f"ESC. 1:{scale}  ·  vigas e contrapiso")
    rows = []
    for i, kk, n in table:
        role, item, L, a1, a2, _bv = kk
        rows.append([i, _cut(ROLE_PT.get(role, role.lower()), 22), item, f"{L}", n])
    ytop = sh.H - M_OTHER - 10
    sh.text(sh.right_x0, ytop + 2, "POSIÇÕES DO ENTREPISO", h=2.0, weight="bold")
    maxr = int((ytop - sh.col_top_free) / 2.8) - 2
    sh.table(sh.right_x0, ytop, ["P", "FUNÇÃO", "ITEM", "CORTE", "QT"], rows, [8, 58, 52, 34, 26], h=1.5, row_h=2.8,
             max_rows=maxr)
    return scale


def _stair_sheet(sh: Sheet, res: Result, st: dict, vnum: int, floor_holes: list):
    """Planta e corte longitudinal da escada, alinhados na mesma escala."""
    x0, y0, x1, y1 = sh.area
    scale = 25
    k = 1 / scale
    n, h, b, run, W = st["n"], st["h"], st["b"], st["run"], st["width"]
    L0, d, ac = st["left0"], st["dir"], st["across"]

    def loc(p):          # global -> local (u ao longo da subida, v na largura)
        dx, dy = p[0] - L0[0], p[1] - L0[1]
        return dx * d[0] + dy * d[1], dx * ac[0] + dy * ac[1]
    umin, umax = -600, run + 900
    ox = x0 + (x1 - x0 - (umax - umin) * k) / 2 - umin * k          # centralizado na área
    grp_h = (W * k + 42) + (st["H"] + 400) * k + 60
    gtop = y1 - max(0.0, (y1 - y0 - grp_h) / 2)
    # ---------- planta
    py = gtop - 12 - W * k
    for hole in floor_holes:
        pts = [loc(p) for p in hole]
        if max(abs(v) for _, v in pts) < 5000:
            sh.poly([(ox + u * k, py + v * k) for u, v in pts], lw=0.25, ec=INK2, fc="none", ls="--", z=2)
    sh.rect(ox, py, run * k, W * k, lw=0.5, ec=INK, fc=sh.pal["soft"], z=3)
    for i in range(1, n):
        ui = i * b
        sh.line([(ox + ui * k, py), (ox + ui * k, py + W * k)], lw=0.25, color=INK, z=4)
        sh.text(ox + (ui - b / 2) * k, py + W * k / 2 - 3.5, str(i), h=1.6, ha="center", kind="mono", z=5)
    for vv in ([0.0, W - 38] if st["stringers"] == 2 else [0.0, (W - 38) / 2, W - 38]):
        sh.rect(ox, py + vv * k, run * k, 38 * k, lw=0.13, ec=INK2, fc="none", z=4)
    ya = py + W * k / 2
    sh.line([(ox + 1.5, ya), (ox + run * k - 3, ya)], lw=0.35, color=sh.pal["primary"], z=6)
    sh.poly([(ox + run * k, ya), (ox + run * k - 3.5, ya + 1.3), (ox + run * k - 3.5, ya - 1.3)], lw=0,
            ec="none", fc=sh.pal["primary"], z=6)
    sh.ax.add_patch(Circle((ox + 1.5, ya), 0.9, color=sh.pal["primary"], zorder=6))
    sh.text(ox + 4, ya + 1.2, "SOBE", h=2.2, weight="bold", color=sh.pal["primary"], z=6)
    for yy in (py - 6, py + W * k + 6):   # linha de corte A-A
        pass
    sh.line([(ox - 10, py + W * k * 0.3), (ox + run * k + 10, py + W * k * 0.3)], lw=0.35, color=INK, ls=(0, (8, 2, 2, 2)), z=6)
    for xx, lab in ((ox - 12, "A"), (ox + run * k + 12, "A")):
        sh.text(xx, py + W * k * 0.3, lab, h=3.2, ha="center", va="center", weight="bold", z=6)
    sh.dim((ox, py), (ox + run * k, py), -6, f"{n - 1} × {b:.0f} = {run:.0f}", h=2.0)
    sh.dim((ox + run * k, py), (ox + run * k, py + W * k), -6, f"{W:.0f}", h=2.0)
    sh.view_title(ox - 20, py - 20, vnum, f"ESCADA {st['id'].split('-')[-1]} — PLANTA", "ESC. 1:25  ·  degraus numerados",
                  w=70)
    # ---------- corte A-A
    fb = (st["floor_bottom"] or st["H"]) - res.stats["levels"][st["low"]]["elevation"]
    sy = py - 42 - (st["H"] + 400) * k
    zmax = st["H"] + 400
    sh.line([(ox + umin * k, sy), (ox + umax * k, sy)], lw=0.7, color=INK, z=5)             # piso de baixo
    sh.rect(ox + umin * k, sy - 4, (umax - umin) * k, 4, lw=0, ec="none", fc="#E4E0D8", hatch="////", z=2)
    # entrepiso (vigas) fora do vão; o vão começa onde a laje acaba sobre a escada
    hole_u = None
    for hole in floor_holes:
        us = [loc(p)[0] for p in hole]
        vs = [loc(p)[1] for p in hole]
        if min(vs) < W and max(vs) > 0:
            hole_u = (min(us), max(us))
    ua = umin if hole_u is None else umin
    if hole_u:
        sh.rect(ox + umin * k, sy + fb * k, (hole_u[0] - umin) * k, (st["H"] - fb) * k, lw=0.35, ec=INK, fc="#EFE7DA",
                hatch="xxxx", z=3)
        sh.rect(ox + hole_u[1] * k, sy + fb * k, (umax - hole_u[1]) * k, (st["H"] - fb) * k, lw=0.35, ec=INK,
                fc="#EFE7DA", hatch="xxxx", z=3)
        sh.text(ox + (umin + 420) * k, sy + st["H"] * k + 2, "ENTREPISO", h=1.8, kind="mono", color=INK2)
    ms = [m for m in res.members if m.parent == st["id"]]
    s1 = next(m for m in ms if m.role == "STRINGER")
    sh.poly([(ox + u * k, sy + z * k) for u, z in s1.polygon], lw=0.35, ec=INK, fc=COLORS.get("HEADER", "#c77"), z=4)
    for m in ms:
        if m.role == "TREAD":
            sh.poly([(ox + u * k, sy + z * k) for u, z in m.polygon], lw=0.3, ec=INK, fc=COLORS.get("BLOCK", "#ddd"), z=5)
    # altura livre: linha 2,00 m acima dos bocéis sob a laje
    nos = [(i * b - (b + st["nosing"]) + b, i * h) for i in range(1, n)]
    sh.line([(ox + u * k, sy + z * k) for u, z in [(0, h), (run, n * h)]], lw=0.18, color=INK2, ls=(0, (6, 3)), z=6)
    u_cut = min(run, max(0.0, (st["H"] + 150 - 2000 - h) * b / h))      # só até pouco acima do entrepiso
    sh.line([(ox + u * k, sy + (h + u * h / b + 2000) * k) for u in (0.0, u_cut)], lw=0.25, color="#C62828",
            ls="--", z=6)
    sh.text(ox + run * k * 0.62, sy + (h + run * 0.62 * h / b) * k + 1.0, "linha dos bocéis", h=1.6, kind="mono",
            color=INK2, rot=st["pitch"], z=6, mask=True, rot_mode="anchor", ha="center", va="bottom")
    sh.text(ox + u_cut * k * 0.25, sy + (h + u_cut * 0.25 * h / b + 2000) * k + 1.0, "2,00 m de altura livre", h=1.6,
            kind="mono", color="#C62828", rot=st["pitch"], z=6, mask=True, rot_mode="anchor", ha="center", va="bottom")
    if st["head_min"] is not None:
        xr_ = ox + ((hole_u[1] if hole_u else run) + 120) * k
        sh.text(xr_, sy + fb * k - 4, f"altura livre mín. {st['head_min']:.0f} mm", h=1.8, ha="left",
                color="#C62828", kind="mono", z=6)
    # cotas
    zs = [i * h for i in range(0, n + 1)]
    sh.dim((ox + umin * k + 6, sy), (ox + umin * k + 6, sy + st["H"] * k), 0, f"{n} × {h:.1f} = {st['H']:.0f}", h=2.0)
    sh.dim((ox, sy), (ox + run * k, sy), -8, f"{n - 1} × {b:.0f} = {run:.0f}", h=2.0)
    sh.dim((ox + b * k, sy + h * k), (ox + b * k, sy + 2 * h * k), -3, f"{h:.1f}", h=1.6)
    sh.dim((ox + b * k, sy + 2 * h * k), (ox + 2 * b * k, sy + 2 * h * k), 3, f"{b:.0f}", h=1.6)
    info = (f"{n} espelhos de {h:.1f} mm  ·  {n - 1} pisos de {b:.0f} mm  ·  Blondel 2h+b = {st['blondel']:.0f} mm  ·  "
            f"inclinação {st['pitch']:.1f}°  ·  garganta da longarina {st['throat']:.0f} mm  ·  bocel {st['nosing']:.0f} mm")
    sh.text(ox + umin * k, sy - 14, info, h=2.0, kind="mono")
    sh.view_title(ox - 20, sy - 26, vnum + 1, f"CORTE A-A — ESCADA {st['id'].split('-')[-1]}",
                  "ESC. 1:25  ·  longarinas recortadas na CNC, pisos colados e pregados", w=90)
    # tabela de peças
    pos, table = _positions(ms)
    rows = [[i, ROLE_PT.get(kk[0], kk[0].lower()), kk[1], f"{kk[2]}", n_] for i, kk, n_ in table]
    ytop = sh.H - M_OTHER - 10
    sh.text(sh.right_x0, ytop + 2, "PEÇAS DA ESCADA", h=2.0, weight="bold")
    sh.table(sh.right_x0, ytop, ["P", "FUNÇÃO", "ITEM", "CORTE", "QT"], rows, [8, 58, 52, 34, 26], h=1.6, row_h=3.0)
