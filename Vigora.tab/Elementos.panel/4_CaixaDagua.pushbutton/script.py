# -*- coding: utf-8 -*-
"""Caixa d'água no ático: adicionar (automática ou clicando), trocar modelo ou remover."""
__title__ = "Caixa\nd'água"
__doc__ = ("Padrão Vigora: ático, apoiada em duas paredes estruturais paralelas a até 1,50 m (hall, banheiro, shaft). "
           "O telhado abre espaço sozinho. Também reconhece uma família com 'Caixa' no nome.")
from pyrevit import revit, forms
import vigora_revit as vr

doc, uidoc = revit.doc, revit.uidoc
if not doc.PathName:
    forms.alert(u"Salve o modelo antes.", exitscript=True)
cfg = vr.ler_config(doc)
tanks = cfg.setdefault("tanks", [])
op = forms.CommandSwitchWindow.show([u"Adicionar (posição automática)", u"Adicionar clicando na planta",
                                     u"Trocar modelo", u"Remover"],
                                    message=u"Caixa d'água (%d no projeto)" % len(tanks))
if not op:
    raise SystemExit
if op.startswith(u"Remover"):
    cfg["tanks"] = []
elif op.startswith(u"Trocar"):
    m = forms.CommandSwitchWindow.show([u"BR_500L", u"BR_1000L"], message=u"Modelo")
    for t in tanks:
        t["model"] = m or t.get("model")
else:
    m = forms.CommandSwitchWindow.show([u"BR_1000L", u"BR_500L"], message=u"Modelo (Fortlev/Tigre)")
    if not m:
        raise SystemExit
    lv = doc.ActiveView.GenLevel
    t = {"id": "CX%d" % (len(tanks) + 1), "model": m, "level_rid": vr.rid(lv.Id) if lv else None}
    if op.endswith(u"planta"):
        p = uidoc.Selection.PickPoint(u"Clique no centro da caixa")
        t["position"] = [p.X * 304.8, p.Y * 304.8]
    cfg["tanks"] = [t]
vr.salvar_config(doc, cfg)
forms.alert(u"Caixa d'água atualizada. Use Verificar para ver apoio e espaço no telhado.", title=u"Vigora")
