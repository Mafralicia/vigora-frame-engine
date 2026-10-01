# -*- coding: utf-8 -*-
"""Verifica o modelo (rápido) e lista os problemas com 'Mostrar no modelo'. Não cria peças."""
__title__ = "Verificar\nmodelo"
__doc__ = "Checa paredes que não encostam, aberturas em encontros, ângulos, telhados, caixa d'água... sem gerar peças."
from pyrevit import revit, forms
import vigora_revit as vr
import vigora_ui as ui

doc, uidoc = revit.doc, revit.uidoc
if not ui.preparar_motor():
    raise SystemExit
if not doc.PathName:
    forms.alert(u"Salve o modelo antes.", exitscript=True)
with forms.ProgressBar(title=u"Vigora: verificando o modelo...", indeterminate=True):
    code, dados, pasta, out = vr.rodar_motor(doc, verificar=True)
if dados is None:
    forms.alert(u"O motor não respondeu. Detalhes:\n\n%s" % (out or u"")[-1500:], title=u"Vigora")
else:
    ui.mostrar_resultados(uidoc, dados, u"Verificação do modelo")
