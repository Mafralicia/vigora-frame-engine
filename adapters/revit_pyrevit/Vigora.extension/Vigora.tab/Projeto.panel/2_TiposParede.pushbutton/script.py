# -*- coding: utf-8 -*-
"""Diz ao motor quais tipos de parede do Revit são portantes e quais são externos (padrão do projeto)."""
__title__ = "Tipos de\nparede"
__doc__ = "Marque os tipos de parede portantes e externos. Vale para todas as paredes daquele tipo."
from pyrevit import revit, forms
from Autodesk.Revit import DB
import vigora_revit as vr

doc = revit.doc
if not doc.PathName:
    forms.alert(u"Salve o modelo antes.", exitscript=True)
usados = {}
for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall).WhereElementIsNotElementType():
    t = doc.GetElement(w.GetTypeId())
    if t is not None:
        usados[t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()] = t
nomes = sorted(usados)
if not nomes:
    forms.alert(u"Nenhuma parede no modelo.", exitscript=True)
cfg = vr.ler_config(doc)
wt = cfg.setdefault("wall_types", {})
ext = forms.SelectFromList.show(nomes, title=u"Quais tipos são EXTERNOS?", multiselect=True, button_name=u"Próximo")
if ext is None:
    raise SystemExit
port = forms.SelectFromList.show(nomes, title=u"Quais tipos são PORTANTES (estruturais)?", multiselect=True,
                                 button_name=u"Salvar")
if port is None:
    raise SystemExit
for n in nomes:
    wt[n] = {"exterior": n in ext, "bearing": n in port}
vr.salvar_config(doc, cfg)
forms.alert(u"%d tipos de parede configurados." % len(nomes), title=u"Vigora")
