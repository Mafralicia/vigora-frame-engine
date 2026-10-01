# -*- coding: utf-8 -*-
"""Escolhas de um telhado: apoio, tipo de treliça, espaçamento, recuo da mestra (4 águas)."""
__title__ = "Telhado"
__doc__ = ("Selecione telhado(s) por perímetro. O tipo (2 águas, 4 águas, meia-água) vem das bordas com caimento; "
           "rincão, encostado, parede alta e platibanda são detectados. Aqui você só força o que quiser.")
from pyrevit import revit, forms
from Autodesk.Revit import DB
import vigora_revit as vr

doc, uidoc = revit.doc, revit.uidoc
sel = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
roofs = [e for e in sel if isinstance(e, DB.FootPrintRoof)]
if not roofs:
    forms.alert(u"Selecione um ou mais telhados (por perímetro) e clique de novo.", exitscript=True)
apoio = forms.CommandSwitchWindow.show([u"Automático", u"Paredes", u"Parede alta (meia-água)", u"Platibanda"],
                                       message=u"Apoio das treliças")
if not apoio:
    raise SystemExit
trel = forms.CommandSwitchWindow.show([u"Automático (pelo vão)", u"fink", u"howe", u"pratt"],
                                      message=u"Tipo de treliça")
if not trel:
    raise SystemExit
esp = forms.CommandSwitchWindow.show([u"Padrão", u"600", u"400"], message=u"Espaçamento (mm)")
recuo = forms.ask_for_string(default=u"", prompt=u"4 águas: recuo da treliça mestra em mm (vazio = automático)",
                             title=u"Vigora — telhado")
cfg = vr.ler_config(doc)
mapa = {u"Paredes": "walls", u"Parede alta (meia-água)": "high_wall", u"Platibanda": "parapet"}
for r in roofs:
    o = cfg.setdefault("roofs", {}).setdefault(str(vr.rid(r.Id)), {})
    o["support"] = mapa.get(apoio)
    o["truss_type"] = None if trel.startswith(u"Autom") else trel
    o["spacing"] = None if (not esp or esp == u"Padrão") else float(esp)
    o["girder_setback"] = float(recuo) if recuo and recuo.strip() else None
vr.salvar_config(doc, cfg)
forms.alert(u"%d telhado(s) configurado(s). Use Verificar ou Gerar." % len(roofs), title=u"Vigora")
