# -*- coding: utf-8 -*-
"""Configurar o projeto: sistema, formato das pranchas, dados da obra e padrões de telhado."""
__title__ = "Configurar\nprojeto"
__doc__ = "Define sistema (wood/steel), formato A1/A0, dados da legenda e padrões de telhado. Uma vez por projeto."
from pyrevit import revit, forms
import vigora_revit as vr
import vigora_ui as ui

doc = revit.doc
if not doc.PathName:
    forms.alert(u"Salve o modelo antes: a configuração fica ao lado do arquivo .rvt.", exitscript=True)
cfg = vr.ler_config(doc)
j = ui.JanelaConfig(cfg)
j.ShowDialog()
if j.ok:
    p = vr.salvar_config(doc, j.cfg)
    forms.toast(u"Configuração salva", title=u"Vigora", appid=u"Vigora")
