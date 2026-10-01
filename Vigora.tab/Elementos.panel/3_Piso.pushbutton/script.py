# -*- coding: utf-8 -*-
"""Direção das vigas do entrepiso (automático = menor vão entre paredes portantes de baixo)."""
__title__ = "Entrepiso"
from pyrevit import revit, forms
from Autodesk.Revit import DB
import vigora_revit as vr

doc, uidoc = revit.doc, revit.uidoc
floors = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
floors = [f for f in floors if isinstance(f, DB.Floor)]
if not floors:
    forms.alert(u"Selecione o piso do pavimento superior e clique de novo.", exitscript=True)
d = forms.CommandSwitchWindow.show([u"Automático", u"Vigas em X", u"Vigas em Y"], message=u"Direção das vigas")
if not d:
    raise SystemExit
cfg = vr.ler_config(doc)
for f in floors:
    cfg.setdefault("floors", {})[str(vr.rid(f.Id))] = {"joist_direction": {u"Vigas em X": "x", u"Vigas em Y": "y"}.get(d)}
vr.salvar_config(doc, cfg)
forms.toast(u"Entrepiso atualizado", title=u"Vigora", appid=u"Vigora")
