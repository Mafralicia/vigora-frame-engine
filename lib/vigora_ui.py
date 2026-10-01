# -*- coding: utf-8 -*-
"""Janelas do plugin (pyRevit WPF). Resultados com "Mostrar no modelo" e configuração do projeto."""
import os

from pyrevit import forms

import vigora_revit as vr

HERE = os.path.dirname(os.path.abspath(__file__))
XAML_RES = os.path.join(HERE, "ui", "resultados.xaml")
XAML_CFG = os.path.join(HERE, "ui", "configurar.xaml")
META = ("cliente", "local", "responsavel_tecnico", "crea", "art", "desenho", "revisao")


class JanelaResultados(forms.WPFWindow):
    """Lista de erros/avisos. 'Mostrar no modelo' fecha a janela, seleciona e dá zoom no elemento."""

    def __init__(self, uidoc, dados, titulo=u"Verificação do modelo"):
        forms.WPFWindow.__init__(self, XAML_RES)
        self.uidoc, self.dados, self.alvo = uidoc, dados, None
        self.titulo.Text = titulo
        self.resumo.Text = vr.resumo_texto(dados)
        self._carregar()

    def _carregar(self):
        self.linhas, self.ids = vr.linhas_resultado(self.dados, so_problemas=bool(self.so_problemas.IsChecked))
        self.lista.ItemsSource = self.linhas if self.linhas else [u"Nenhum erro ou aviso. Modelo pronto para gerar."]

    def filtrar(self, sender, args):
        self._carregar()

    def mostrar(self, sender, args):
        i = self.lista.SelectedIndex
        if 0 <= i < len(self.ids) and self.ids[i]:
            self.alvo = self.ids[i]
            self.Close()
        elif 0 <= i < len(self.ids):
            forms.alert(u"Este item não aponta para um elemento específico do modelo.", title=u"Vigora")

    def copiar(self, sender, args):
        import clr
        clr.AddReference("PresentationCore")
        from System.Windows import Clipboard
        Clipboard.SetText(u"\n".join(self.linhas))

    def fechar(self, sender, args):
        self.Close()


def mostrar_resultados(uidoc, dados, titulo=u"Verificação do modelo"):
    """Abre a lista; se o usuário pedir 'Mostrar', seleciona o elemento e reabre a lista (fluxo de correção)."""
    while True:
        j = JanelaResultados(uidoc, dados, titulo)
        j.ShowDialog()
        if not j.alvo:
            return
        vr.mostrar_elementos(uidoc, j.alvo)
        if not forms.alert(u"Elemento selecionado no modelo.\nVoltar para a lista?", yes=True, no=True,
                           title=u"Vigora"):
            return


class JanelaConfig(forms.WPFWindow):
    def __init__(self, cfg):
        forms.WPFWindow.__init__(self, XAML_CFG)
        self.cfg, self.ok = cfg, False
        self._sel(self.sistema, cfg.get("system", "wood"))
        self._sel(self.formato, cfg.get("formato", "A1"))
        self.pranchas.IsChecked = bool(cfg.get("pranchas", True))
        for k in META:
            getattr(self, k).Text = cfg.get("meta", {}).get(k, u"")
        rd = cfg.get("roof_defaults", {})
        self._sel(self.truss_type, rd.get("truss_type") or u"Automático (pelo vão)")
        self._sel(self.spacing, str(rd.get("spacing")) if rd.get("spacing") else u"Padrão das regras")
        self.overhang.Text = str(rd.get("overhang") or u"")

    @staticmethod
    def _sel(combo, valor):
        for i in range(combo.Items.Count):
            if combo.Items[i].Content == valor:
                combo.SelectedIndex = i
                return
        combo.SelectedIndex = 0

    def salvar(self, sender, args):
        c = self.cfg
        c["system"] = self.sistema.SelectedItem.Content
        c["ruleset"] = "wood-br-v1" if c["system"] == "wood" else "steel-br-v1"
        c["formato"] = self.formato.SelectedItem.Content
        c["pranchas"] = bool(self.pranchas.IsChecked)
        c.setdefault("meta", {})
        for k in META:
            c["meta"][k] = getattr(self, k).Text.strip()
        tt = self.truss_type.SelectedItem.Content
        sp = self.spacing.SelectedItem.Content
        ov = self.overhang.Text.strip()
        c["roof_defaults"] = {"truss_type": None if tt.startswith(u"Autom") else tt,
                              "spacing": None if sp.startswith(u"Padr") else float(sp),
                              "overhang": float(ov) if ov else None}
        self.ok = True
        self.Close()

    def cancelar(self, sender, args):
        self.Close()


def preparar_motor():
    """Garante Python 3.11+ e as bibliotecas do motor. Retorna True se pode rodar."""
    py = vr.python_cmd()
    if py is None:
        forms.alert(u"O motor da Vigora precisa do Python 3.11 ou mais novo (uma vez por computador).\n\n"
                    u"Instale em python.org (marque 'Add python.exe to PATH') e clique de novo.",
                    title=u"Vigora — Python não encontrado")
        return False
    if vr.dependencias_ok(py):
        return True
    if not forms.alert(u"Primeiro uso neste computador: faltam bibliotecas do motor (pydantic, shapely, "
                       u"matplotlib...).\n\nInstalar agora? Leva 1 a 3 minutos.", yes=True, no=True,
                       title=u"Vigora — preparar o motor"):
        return False
    with forms.ProgressBar(title=u"Vigora: instalando bibliotecas do motor...", indeterminate=True):
        code, out = vr.instalar_dependencias(py)
    if vr.dependencias_ok(py):
        forms.toast(u"Motor pronto", title=u"Vigora", appid=u"Vigora")
        return True
    txt = out.decode("utf-8", "ignore") if isinstance(out, bytes) else (out or u"")
    forms.alert(u"Não foi possível instalar as bibliotecas. Detalhes:\n\n" + txt[-1500:], title=u"Vigora")
    return False
