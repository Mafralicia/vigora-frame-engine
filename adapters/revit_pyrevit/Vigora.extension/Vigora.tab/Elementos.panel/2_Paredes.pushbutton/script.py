# -*- coding: utf-8 -*-
"""Marcações por parede (vencem o padrão do tipo): portante/não portante, externa/interna."""
__title__ = "Paredes"
from pyrevit import revit, forms
from Autodesk.Revit import DB
import vigora_revit as vr

doc, uidoc = revit.doc, revit.uidoc
walls = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
walls = [w for w in walls if isinstance(w, DB.Wall)]
if not walls:
    forms.alert(u"Selecione uma ou mais paredes e clique de novo.", exitscript=True)
op = forms.CommandSwitchWindow.show([u"Portante", u"Não portante", u"Externa", u"Interna", u"Limpar marcações"],
                                    message=u"%d parede(s) selecionada(s)" % len(walls))
if not op:
    raise SystemExit
cfg = vr.ler_config(doc)
for w in walls:
    k = str(vr.rid(w.Id))
    o = cfg.setdefault("walls", {}).setdefault(k, {})
    if op == u"Portante":
        o["bearing"] = True
    elif op == u"Não portante":
        o["bearing"] = False
    elif op == u"Externa":
        o["exterior"] = True
    elif op == u"Interna":
        o["exterior"] = False
    else:
        cfg["walls"].pop(k, None)
vr.salvar_config(doc, cfg)
forms.toast(u"Paredes atualizadas", title=u"Vigora", appid=u"Vigora")
