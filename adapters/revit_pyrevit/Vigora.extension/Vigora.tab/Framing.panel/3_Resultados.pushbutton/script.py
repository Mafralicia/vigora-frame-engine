# -*- coding: utf-8 -*-
"""Reabre a última lista de erros e avisos (sem rodar de novo)."""
__title__ = "Últimos\nresultados"
from pyrevit import revit, forms
import vigora_revit as vr
import vigora_ui as ui

dados = vr.ler_verificacao(vr.pasta_saida(revit.doc))
if not dados:
    forms.alert(u"Ainda não há resultados. Use Verificar ou Gerar.", exitscript=True)
ui.mostrar_resultados(revit.uidoc, dados, u"Últimos resultados")
