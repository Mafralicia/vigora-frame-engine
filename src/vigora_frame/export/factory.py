"""Arquivos de fábrica: CSV de peças e de máquina, DXF de painéis e treliças, etiquetas."""
from __future__ import annotations

import csv
import io

import ezdxf
import qrcode
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from ..model import Result


def write_csv(res: Result, q: dict, folder) -> list[str]:
    out = []
    p = f"{folder}/pecas.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "funcao", "item", "grupo", "pai", "corte_mm", "camadas", "angulo_a", "angulo_b", "x0", "x1",
                    "z0", "z1", "especial", "regra", "obs"])
        for m in res.members:
            w.writerow([m.id, m.role, m.item, m.group, m.parent, m.cut_length, m.plies, m.angle_a, m.angle_b,
                        m.x0, m.x1, m.z0, m.z1, int(m.special), m.rule, m.note])
    out.append(p)
    p = f"{folder}/lista_corte.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["item", "barra", "comprimento_barra", "ordem", "corte_mm", "peca_id"])
        for item, plan in q["cut_plan"].items():
            for bi, b in enumerate(plan["bars"], start=1):
                for k, (pid, L) in enumerate(b.cuts, start=1):
                    w.writerow([item, bi, b.stock, k, round(L, 1), pid])
    out.append(p)
    # formato genérico de máquina: uma linha por peça de painel, com posição na mesa
    p = f"{folder}/maquina_generico.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["painel", "sequencia", "peca_id", "funcao", "item", "comprimento", "angulo_a", "angulo_b",
                    "pos_x", "pos_z", "orientacao", "camadas"])
        order = {"BOTTOM_PLATE": 0, "TOP_PLATE": 0, "STUD_END": 1, "STUD": 1, "KING": 1, "BACKER": 1, "SHEET_STUD": 1,
                 "JACK": 2, "HEADER": 3, "SILL": 3, "CRIPPLE": 4, "NAILER": 4, "BLOCK": 5, "PACKER": 5}
        for pan in res.panels:
            ms = [m for m in res.members if m.parent == pan.id]
            ms.sort(key=lambda m: (order.get(m.role, 9), m.x0, m.z0))
            for k, m in enumerate(ms, start=1):
                w.writerow([pan.id, k, m.id, m.role, m.item, m.cut_length, m.angle_a, m.angle_b, m.x0, m.z0,
                            m.orientation, m.plies])
    out.append(p)
    return out


def write_dxf(res: Result, path: str) -> None:
    doc = ezdxf.new("R2010", setup=True)
    msp = doc.modelspace()
    for name, color in (("PECAS", 30), ("PLACAS", 5), ("CNC", 6), ("TEXTO", 7), ("TRELICAS", 40), ("FACE", 8)):
        doc.layers.add(name, color=color)
    y = 0.0
    for pan in res.panels:
        ms = [m for m in res.members if m.parent == pan.id]
        for m in ms:
            if m.polygon:
                pts = [(x, y + z) for x, z in m.polygon]
                layer = "CNC" if m.special else "FACE"
            else:
                pts = [(m.x0, y + m.z0), (m.x1, y + m.z0), (m.x1, y + m.z1), (m.x0, y + m.z1)]
                layer = "FACE" if m.plane == "face" else "PECAS"
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        for s in [s for s in res.sheets if s.parent == pan.id]:
            msp.add_lwpolyline([(s.x0, y + s.z0), (s.x1, y + s.z0), (s.x1, y + s.z1), (s.x0, y + s.z1)], close=True,
                               dxfattribs={"layer": "PLACAS", "linetype": "DASHED"})
        msp.add_text(f"{pan.id}  L={pan.length:.0f}  H={pan.height:.0f}  {pan.weight_kg:.0f} kg",
                     dxfattribs={"layer": "TEXTO", "height": 80}).set_placement((0, y - 200))
        y += pan.height + 800
    x = 0.0
    for tm in res.trusses:
        ms = [m for m in res.members if m.id in set(tm.member_ids)]
        for m in ms:
            msp.add_lwpolyline([(x + px, y + py) for px, py in m.polygon], close=True, dxfattribs={"layer": "TRELICAS"})
        msp.add_text(f"TRELICA {tm.mark} {tm.type} x{tm.count}", dxfattribs={"layer": "TEXTO", "height": 100}).set_placement((x, y - 250))
        x += tm.span + 2500
    doc.saveas(path)


def _qr(data: str):
    img = qrcode.make(data, box_size=4, border=1)
    b = io.BytesIO()
    img.save(b, format="PNG")
    b.seek(0)
    return ImageReader(b)


def write_labels(res: Result, pdf_path: str, zpl_path: str) -> None:
    """Etiqueta de painel 100 x 70 mm (PDF) e etiqueta de peça em ZPL (Zebra, 100 x 50 mm)."""
    W, H = 100 * mm, 70 * mm
    c = canvas.Canvas(pdf_path, pagesize=(W, H))
    status = "APROVADO" if res.ruleset_approved else "RASCUNHO"
    for p in res.panels:
        c.setFont("Helvetica-Bold", 13)
        c.drawString(5 * mm, H - 10 * mm, p.id.split("-", 1)[-1])
        c.setFont("Helvetica", 8)
        c.drawString(5 * mm, H - 16 * mm, f"Projeto {res.project} · parede {p.wall} · nível {p.level}")
        c.drawString(5 * mm, H - 21 * mm, f"Tipo {p.wall_type} · {p.length:.0f} x {p.height:.0f} mm")
        c.drawString(5 * mm, H - 26 * mm, f"Peso {p.weight_kg:.0f} kg · {len(p.member_ids)} peças")
        c.drawString(5 * mm, H - 31 * mm, f"Assinatura {p.signature}")
        c.drawString(5 * mm, H - 36 * mm, f"Execução {res.run_id}")
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.78, 0.16, 0.16) if not res.ruleset_approved else c.setFillColorRGB(0.18, 0.49, 0.2)
        c.drawString(5 * mm, 6 * mm, status)
        c.setFillColorRGB(0, 0, 0)
        c.drawImage(_qr(f"VFE|{res.project}|{p.id}|{p.signature}|{res.run_id}"), W - 38 * mm, 8 * mm, 33 * mm, 33 * mm)
        c.showPage()
    c.save()
    with open(zpl_path, "w", encoding="utf-8") as f:
        for m in res.members:
            if m.frame not in ("panel", "truss"):
                continue
            f.write("^XA^CI28\n")
            f.write(f"^FO30,25^A0N,34,34^FD{m.id.split('-', 2)[-1][:38]}^FS\n")
            f.write(f"^FO30,70^A0N,26,26^FD{m.item}  L={m.cut_length:.0f} mm  {m.angle_a:.0f}/{m.angle_b:.0f}^FS\n")
            f.write(f"^FO30,105^A0N,24,24^FD{m.parent.split('-', 1)[-1][:40]}^FS\n")
            f.write(f"^FO30,140^A0N,24,24^FD{'RASCUNHO' if not res.ruleset_approved else ''}^FS\n")
            f.write(f"^FO600,20^BQN,2,4^FDLA,VFE|{m.id}|{res.run_id}^FS\n")
            f.write("^XZ\n")
