# -*- coding: utf-8 -*-
"""Gera o framing do projeto inteiro: peças 3D no modelo + planilha, pranchas e arquivos de máquina."""
__title__ = "Gerar\nframing"
__doc__ = "Projeto inteiro, sem seleção. Na segunda vez atualiza só o que mudou."
from pyrevit import revit, forms
import vigora_revit as vr
import vigora_ui as ui

doc, uidoc = revit.doc, revit.uidoc
if not doc.PathName:
    forms.alert(u"Salve o modelo antes.", exitscript=True)
with forms.ProgressBar(title=u"Vigora: gerando o framing (pode levar 1 minuto)...", indeterminate=True):
    code, dados, pasta, out = vr.rodar_motor(doc, verificar=False)
if dados is None:
    forms.alert(u"O motor não gerou saída. Detalhes:\n\n%s" % (out or u"")[-1500:], title=u"Vigora", exitscript=True)
r = vr.aplicar_da_pasta(doc, pasta)
msg = vr.resumo_texto(dados)
if r:
    msg += u"\n\nNo modelo: %(criados)d criadas · %(mantidos)d mantidas · %(apagados)d apagadas" % r
    if r["falhas"]:
        msg += u" · %d falhas" % r["falhas"]
if dados["summary"]["errors"] or dados["summary"]["warnings"]:
    forms.alert(msg + u"\n\nA seguir: lista de erros e avisos.", title=u"Vigora — framing gerado")
    ui.mostrar_resultados(uidoc, dados, u"Framing gerado")
else:
    forms.alert(msg + u"\n\nSaídas em:\n" + pasta, title=u"Vigora — framing gerado")
