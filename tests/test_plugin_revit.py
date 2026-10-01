"""Plugin Revit (sem Revit): compatibilidade IronPython, telas, biblioteca com API simulada e comando do motor."""
import ast
import json
import re
import subprocess
import sys
import types
import xml.etree.ElementTree as ET

import pytest

from conftest import ROOT

EXT = ROOT / "adapters" / "revit_pyrevit" / "Vigora.extension"
PY_FILES = sorted(EXT.rglob("*.py"))


def test_plugin_files_exist():
    names = {p.parent.name for p in PY_FILES if p.name == "script.py"}
    assert {"1_Configurar.pushbutton", "1_Verificar.pushbutton", "2_Gerar.pushbutton", "1_Telhado.pushbutton",
            "4_CaixaDagua.pushbutton", "1_Pranchas.pushbutton"} <= names
    for p in PY_FILES:
        if p.name == "script.py":
            assert (p.parent / "icon.png").exists(), p


@pytest.mark.parametrize("path", PY_FILES, ids=lambda p: str(p.relative_to(EXT)))
def test_ironpython_compatible_syntax(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr), f"f-string em {path}"            # IronPython 2.7
        assert not isinstance(node, ast.AnnAssign), f"anotação de tipo em {path}"
        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            a = node.args
            assert not a.kwonlyargs and all(x.annotation is None for x in a.args), f"assinatura py3 em {path}"
        assert not isinstance(node, ast.Nonlocal)


def test_xaml_well_formed_and_handlers_exist():
    ui_src = (EXT / "lib" / "vigora_ui.py").read_text(encoding="utf-8")
    methods = set(re.findall(r"def (\w+)\(self", ui_src))
    for xf in (EXT / "lib" / "ui").glob("*.xaml"):
        root = ET.parse(xf).getroot()
        for el in root.iter():
            for attr in ("Click", "MouseDoubleClick"):
                if attr in el.attrib:
                    assert el.attrib[attr] in methods, f"{xf.name}: {el.attrib[attr]}"
        names = {el.attrib.get("{http://schemas.microsoft.com/winfx/2006/xaml}Name") for el in root.iter()}
        for used in re.findall(r"self\.(\w+)\.(?:Text|IsChecked|SelectedIndex|SelectedItem|ItemsSource|Items)", ui_src):
            if xf.name == "configurar.xaml" and used in ("lista", "so_problemas", "titulo", "resumo"):
                continue
            if xf.name == "resultados.xaml" and used not in ("lista", "so_problemas", "titulo", "resumo"):
                continue
            assert used in names or used in ("cliente", "local", "responsavel_tecnico", "crea", "art", "desenho",
                                             "revisao"), f"{xf.name}: {used}"


@pytest.fixture
def vr(monkeypatch):
    rev = types.ModuleType("Autodesk.Revit")
    rev.DB = types.SimpleNamespace(ElementId=lambda x: x)
    monkeypatch.setitem(sys.modules, "Autodesk", types.ModuleType("Autodesk"))
    monkeypatch.setitem(sys.modules, "Autodesk.Revit", rev)
    monkeypatch.syspath_prepend(str(EXT / "lib"))
    sys.modules.pop("vigora_revit", None)
    import vigora_revit
    yield vigora_revit
    sys.modules.pop("vigora_revit", None)            # não vazar a API simulada para outros testes


def test_element_id_revit_2024_and_older(vr):
    novo = types.SimpleNamespace(Id=types.SimpleNamespace(Value=9123456789012))      # Revit 2024+: Int64
    velho = types.SimpleNamespace(Id=types.SimpleNamespace(IntegerValue=311))       # até 2023
    assert vr.rid(novo) == 9123456789012 and vr.rid(velho) == 311
    assert vr.rid(types.SimpleNamespace(Value=5)) == 5


def test_config_next_to_rvt_and_result_lines(vr, tmp_path):
    doc = types.SimpleNamespace(PathName=str(tmp_path / "Casa 01.rvt"), Title="Casa 01")
    cfg = vr.ler_config(doc)
    assert cfg["system"] == "wood" and cfg["tanks"] == []
    cfg["walls"]["123"] = {"bearing": False}
    p = vr.salvar_config(doc, cfg)
    assert p.endswith("Casa 01.vigora.json") and vr.ler_config(doc)["walls"]["123"] == {"bearing": False}
    assert vr.pasta_saida(doc).endswith("Casa 01_vigora")
    dados = {"summary": {"errors": 1, "warnings": 0, "panels": 3, "members": 40, "trusses": 5, "pages": 0,
                         "approved": False},
             "issues": [{"severity": "error", "code": "V-075", "message": "folga", "rids": [10], "hint": "una"},
                        {"severity": "info", "code": "V-000", "message": "ok", "rids": []}]}
    linhas, ids = vr.linhas_resultado(dados, so_problemas=True)
    assert len(linhas) == 1 and "V-075" in linhas[0] and "una" in linhas[0] and ids == [[10]]
    assert "RASCUNHO" in vr.resumo_texto(dados)
    unsaved = types.SimpleNamespace(PathName="", Title="x")
    with pytest.raises(RuntimeError):
        vr.salvar_config(unsaved, cfg)


def test_engine_command_used_by_plugin(tmp_path):
    sys.path.insert(0, str(ROOT / "tests"))
    from test_revit_import import fake_raw
    from vigora_frame.builder import load_project
    raw = fake_raw(load_project(ROOT / "examples" / "casa_caixa_dagua.json"))
    raw["tanks"] = []
    (tmp_path / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
    cfg = {"system": "wood", "tanks": [{"id": "CX1", "model": "BR_500L", "level_rid": raw["levels"][0]["rid"]}],
           "meta": {"cliente": "Teste"}}
    (tmp_path / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
    out = subprocess.run([sys.executable, "-m", "vigora_frame.cli", "revit", str(tmp_path / "raw.json"), "--config",
                          str(tmp_path / "cfg.json"), "--out", str(tmp_path / "o"), "--verificar"],
                         capture_output=True, text=True, env={"PYTHONPATH": str(ROOT / "src")}, cwd=ROOT)
    assert out.returncode == 0, out.stdout + out.stderr
    v = json.loads((tmp_path / "o" / "verificacao.json").read_text(encoding="utf-8"))
    assert v["summary"]["errors"] == 0 and any("caixa 500 L" in i["message"] for i in v["issues"])
    proj = json.loads((tmp_path / "o" / "projeto.json").read_text(encoding="utf-8"))
    assert proj["meta"]["cliente"] == "Teste" and proj["tanks"][0]["model"] == "BR_500L"
