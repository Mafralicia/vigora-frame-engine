# -*- coding: utf-8 -*-
"""Gera as pranchas (A1 ou A0) e abre o PDF."""
__title__ = "Pranchas"
import os
from pyrevit import revit, forms
import vigora_revit as vr
import vigora_ui as ui

doc = revit.doc
if not ui.preparar_motor():
    raise SystemExit
cfg = vr.ler_config(doc)
fmt = forms.CommandSwitchWindow.show([u"A1", u"A0"], message=u"Formato das pranchas")
if not fmt:
    raise SystemExit
cfg["formato"], cfg["pranchas"] = fmt, True
vr.salvar_config(doc, cfg)
with forms.ProgressBar(title=u"Vigora: gerando pranchas %s..." % fmt, indeterminate=True):
    code, dados, pasta, out = vr.rodar_motor(doc, verificar=False)
pdf = os.path.join(pasta, u"pranchas_%s.pdf" % fmt)
if os.path.exists(pdf):
    os.startfile(pdf)
else:
    forms.alert(u"Pranchas não geradas. Detalhes:\n\n%s" % (out or u"")[-1500:], title=u"Vigora")
