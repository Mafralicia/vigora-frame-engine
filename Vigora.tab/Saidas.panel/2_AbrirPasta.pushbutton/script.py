# -*- coding: utf-8 -*-
"""Abre a pasta de saídas (planilha, pranchas, arquivos de máquina, etiquetas)."""
__title__ = "Abrir\nsaídas"
import os
from pyrevit import revit, forms
import vigora_revit as vr

p = vr.pasta_saida(revit.doc)
if os.path.isdir(p):
    os.startfile(p)
else:
    forms.alert(u"Ainda não há saídas. Use Gerar framing.", title=u"Vigora")
