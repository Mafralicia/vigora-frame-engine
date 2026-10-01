# -*- coding: utf-8 -*-
"""Plugin Revit do Vigora Frame Engine (pyRevit) — camada fina dentro do Revit.

Compatível com IronPython 2.7/3.4 e CPython do pyRevit, Revit 2024–2026 (ElementId de 64 bits).
NÃO TESTADO EM REVIT REAL: a lógica pesada roda no motor (CPython) e é testada lá; aqui só se extraem
dados brutos em mm, se guarda a configuração e se aplicam os sólidos.

Fluxo de cada botão:
  extrair_bruto(doc) -> raw.json  +  <modelo>.vigora.json (configuração)
  motor: python -m vigora_frame.cli revit raw.json --config cfg --out pasta [--verificar]
  verificacao.json (erros com ids do Revit)  e  revit_solidos.json (peças 3D)
  aplicar_solidos(doc, dados): DirectShape por peça, atualização por diferença.
"""
from __future__ import print_function
import io
import json
import math
import os

from Autodesk.Revit import DB

MM = 1.0 / 304.8           # mm -> pés
APP_ID = "VigoraFrameEngine"
TANK_FAMILY_KEYS = ("caixa", "tank", "reservat")


# ------------------------------------------------------------------ compatibilidade de versões
def rid(x):
    """ElementId (ou elemento) -> inteiro. Revit 2024+: .Value (Int64); antes: .IntegerValue."""
    i = getattr(x, "Id", x)
    v = getattr(i, "Value", None)
    if v is not None:
        return int(v)
    return int(i.IntegerValue)


def to_eid(n):
    try:
        import System
        return DB.ElementId(System.Int64(n))
    except Exception:
        return DB.ElementId(int(n))


def _mm(feet):
    return feet * 304.8


def _xy(p):
    return [round(_mm(p.X), 1), round(_mm(p.Y), 1)]


def _param(el, bip, default=None):
    p = el.get_Parameter(bip)
    if p is None or not p.HasValue:
        return default
    return p.AsDouble()


def _type_param(el, bip):
    sym = el.Symbol if hasattr(el, "Symbol") else None
    for src in (el, sym):
        if src is None:
            continue
        p = src.get_Parameter(bip)
        if p is not None and p.HasValue and p.AsDouble() > 0:
            return p.AsDouble()
    return None


def _level_elev(doc, lid):
    lv = doc.GetElement(lid)
    return lv.Elevation if lv is not None else 0.0


# ------------------------------------------------------------------ extração bruta (mm)
def extrair_bruto(doc):
    raw = {"doc": {"title": doc.Title, "path": doc.PathName}, "levels": [], "walls": [], "roofs": [], "floors": [],
           "stairs": [], "tanks": [], "unsupported": []}
    for lv in DB.FilteredElementCollector(doc).OfClass(DB.Level):
        raw["levels"].append({"rid": rid(lv.Id), "name": lv.Name, "elevation": round(_mm(lv.Elevation), 1)})
    for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall).WhereElementIsNotElementType():
        d = _parede(doc, w)
        if d:
            raw["walls"].append(d)
    for r in DB.FilteredElementCollector(doc).OfClass(DB.RoofBase).WhereElementIsNotElementType():
        d = _telhado(doc, r)
        if d:
            raw["roofs"].append(d)
        else:
            raw["unsupported"].append({"rid": rid(r.Id), "what": "telhado que não é por perímetro"})
    for f in DB.FilteredElementCollector(doc).OfClass(DB.Floor).WhereElementIsNotElementType():
        d = _piso(doc, f)
        if d:
            raw["floors"].append(d)
    try:
        from Autodesk.Revit.DB.Architecture import Stairs
        for s in DB.FilteredElementCollector(doc).OfClass(Stairs).WhereElementIsNotElementType():
            d = _escada(doc, s)
            if d:
                raw["stairs"].append(d)
    except Exception:
        pass
    for fi in DB.FilteredElementCollector(doc).OfClass(DB.FamilyInstance).WhereElementIsNotElementType():
        d = _caixa(doc, fi)
        if d:
            raw["tanks"].append(d)
    return raw


def _parede(doc, w):
    loc = w.Location
    if loc is None or not hasattr(loc, "Curve"):
        return None
    c = loc.Curve
    wt = doc.GetElement(w.GetTypeId())
    base_off = _param(w, DB.BuiltInParameter.WALL_BASE_OFFSET, 0.0)
    top_p = w.get_Parameter(DB.BuiltInParameter.WALL_HEIGHT_TYPE)
    top_lv = top_p.AsElementId() if top_p is not None else None
    if top_lv is not None and rid(top_lv) > 0:
        h = (_level_elev(doc, top_lv) + _param(w, DB.BuiltInParameter.WALL_TOP_OFFSET, 0.0)) - \
            (_level_elev(doc, w.LevelId) + base_off)
    else:
        h = _param(w, DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM, 2700 * MM)
    est = w.get_Parameter(DB.BuiltInParameter.WALL_STRUCTURAL_SIGNIFICANT)
    func = "Exterior" if (wt is not None and wt.Function == DB.WallFunction.Exterior) else "Interior"
    keyref = w.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM)
    tname = ""
    if wt is not None:
        tp = wt.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
        tname = tp.AsString() if tp is not None else ""
    d = {"rid": rid(w.Id), "level_rid": rid(w.LevelId), "type_name": tname, "type_function": func,
         "structural": bool(est.AsInteger()) if est is not None else func == "Exterior",
         "width": round(_mm(w.Width), 1), "location_line": keyref.AsInteger() if keyref is not None else 0,
         "orientation": [round(w.Orientation.X, 6), round(w.Orientation.Y, 6)], "height": round(_mm(h), 1),
         "base_offset": round(_mm(base_off), 1), "inserts": []}
    if isinstance(c, DB.Arc):
        cen = c.Center
        a0, a1 = c.GetEndPoint(0), c.GetEndPoint(1)

        def ang(p):
            return math.degrees(math.atan2(p.Y - cen.Y, p.X - cen.X))
        d["curve"] = {"kind": "arc", "center": _xy(cen), "radius": round(_mm(c.Radius), 1), "a0": ang(a0), "a1": ang(a1)}
        return d
    p0, p1 = c.GetEndPoint(0), c.GetEndPoint(1)
    d["curve"] = {"kind": "line", "p0": _xy(p0), "p1": _xy(p1)}
    dirv = (p1 - p0).Normalize()
    for fid in w.FindInserts(True, False, False, False):
        fi = doc.GetElement(fid)
        if not isinstance(fi, DB.FamilyInstance) or fi.Location is None or fi.Category is None:
            continue
        cat = rid(fi.Category.Id)
        if cat not in (int(DB.BuiltInCategory.OST_Doors), int(DB.BuiltInCategory.OST_Windows)):
            continue
        larg = (_type_param(fi, DB.BuiltInParameter.FAMILY_WIDTH_PARAM) or
                _type_param(fi, DB.BuiltInParameter.DOOR_WIDTH) or _type_param(fi, DB.BuiltInParameter.WINDOW_WIDTH))
        alt = (_type_param(fi, DB.BuiltInParameter.FAMILY_HEIGHT_PARAM) or
               _type_param(fi, DB.BuiltInParameter.DOOR_HEIGHT) or _type_param(fi, DB.BuiltInParameter.WINDOW_HEIGHT))
        if not larg or not alt:
            continue
        porta = cat == int(DB.BuiltInCategory.OST_Doors)
        sill = 0.0 if porta else _param(fi, DB.BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM, 0.0)
        d["inserts"].append({"rid": rid(fi.Id), "category": "door" if porta else "window",
                             "center_along": round(_mm((fi.Location.Point - p0).DotProduct(dirv)), 1),
                             "width": round(_mm(larg), 1), "height": round(_mm(alt), 1), "sill": round(_mm(sill), 1)})
    return d


def _telhado(doc, r):
    if not isinstance(r, DB.FootPrintRoof):
        return None
    edges = []
    profiles = r.GetProfiles()
    for i in range(profiles.Size):
        arr = profiles.get_Item(i)
        for j in range(arr.Size):
            mc = arr.get_Item(j)
            cv = mc.GeometryCurve
            slope = bool(r.get_DefinesSlope(mc))
            ang = 0.0
            if slope:
                v = r.get_SlopeAngle(mc)          # CONFIRMAR NO 1º TESTE: tangente (subida/percurso)
                ang = math.degrees(math.atan(v))
            edges.append({"p0": _xy(cv.GetEndPoint(0)), "p1": _xy(cv.GetEndPoint(1)), "slope": slope,
                          "angle_deg": round(ang, 3)})
    return {"rid": rid(r.Id), "level_rid": rid(r.LevelId), "edges": edges,
            "base_offset": round(_mm(_param(r, DB.BuiltInParameter.ROOF_LEVEL_OFFSET_PARAM, 0.0)), 1)}


def _laco(curves):
    return [_xy(cv.GetEndPoint(0)) for cv in curves]


def _piso(doc, f):
    try:
        prof = doc.GetElement(f.SketchId).Profile
    except Exception:
        return None
    loops = [_laco(list(prof.get_Item(i))) for i in range(prof.Size)]
    for op in DB.FilteredElementCollector(doc).OfClass(DB.Opening):
        try:
            if op.Host is not None and rid(op.Host.Id) == rid(f.Id):
                loops.append(_laco(list(op.BoundaryCurves)))
        except Exception:
            pass
    return {"rid": rid(f.Id), "level_rid": rid(f.LevelId), "loops": loops}


def _escada(doc, s):
    runs = []
    for run_id in s.GetStairsRuns():
        run = doc.GetElement(run_id)
        path = list(run.GetStairsPath())
        if path:
            runs.append({"start": _xy(path[0].GetEndPoint(0)), "end": _xy(path[-1].GetEndPoint(1)),
                         "width": round(_mm(run.ActualRunWidth), 1)})
    base = s.get_Parameter(DB.BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)
    top = s.get_Parameter(DB.BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)
    return {"rid": rid(s.Id), "base_level_rid": rid(base.AsElementId()) if base else None,
            "top_level_rid": rid(top.AsElementId()) if top else None, "runs": runs}


def _caixa(doc, fi):
    try:
        fam = fi.Symbol.Family.Name.lower()
    except Exception:
        return None
    if not any(k in fam for k in TANK_FAMILY_KEYS) or fi.Location is None or not hasattr(fi.Location, "Point"):
        return None
    modelo = None
    p = fi.Symbol.LookupParameter("Modelo") or fi.LookupParameter("Modelo")
    if p is not None and p.HasValue:
        modelo = p.AsString()
    if not modelo:
        np_ = fi.Symbol.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
        nome = (np_.AsString() if np_ is not None else "") or ""
        modelo = "BR_500L" if "500" in nome else "BR_1000L"
    return {"rid": rid(fi.Id), "level_rid": rid(fi.LevelId), "model": modelo, "point": _xy(fi.Location.Point)}


# ------------------------------------------------------------------ configuração do projeto (ao lado do .rvt)
PADRAO = {"system": "wood", "formato": "A1", "pranchas": True, "meta": {}, "roof_defaults": {},
          "wall_types": {}, "walls": {}, "roofs": {}, "floors": {}, "tanks": []}


def caminho_config(doc):
    if not doc.PathName:
        return None
    return os.path.splitext(doc.PathName)[0] + ".vigora.json"


def pasta_saida(doc):
    base = os.path.splitext(doc.PathName)[0] if doc.PathName else os.path.join(os.path.expanduser("~"), "vigora")
    return base + "_vigora"


def ler_config(doc):
    cfg = json.loads(json.dumps(PADRAO))
    p = caminho_config(doc)
    if p and os.path.exists(p):
        with io.open(p, encoding="utf-8") as f:
            cfg.update(json.load(f))
    return cfg


def salvar_config(doc, cfg):
    p = caminho_config(doc)
    if not p:
        raise RuntimeError("Salve o modelo (.rvt) antes: a configuração fica ao lado do arquivo.")
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=1))
    return p


# ------------------------------------------------------------------ motor (CPython externo)
# A raiz do repositório É a extensão (Vigora.extension): Vigora.tab/, lib/ e o motor em src/.
EXT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPS_IMPORT = "import pydantic, yaml, shapely, openpyxl, matplotlib, reportlab, ezdxf, qrcode, typer"
CREATE_NO_WINDOW = 0x08000000


def _run(cmd, env=None, timeout=None):
    import subprocess
    kw = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT, "cwd": EXT_ROOT}
    if os.name == "nt":
        kw["creationflags"] = CREATE_NO_WINDOW
    if env:
        kw["env"] = env
    try:
        p = subprocess.Popen(cmd, **kw)
    except TypeError:                         # IronPython antigo sem creationflags
        kw.pop("creationflags", None)
        try:
            p = subprocess.Popen(cmd, **kw)
        except Exception as ex:
            return -1, str(ex)
    except Exception as ex:
        return -1, str(ex)
    out, _ = p.communicate()
    return p.returncode, out


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(EXT_ROOT, "src")
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _python_ok(cmd):
    code, out = _run(cmd + ["-c", "import sys; print(sys.version_info[:2] >= (3, 11))"])
    return code == 0 and b"True" in (out if isinstance(out, bytes) else out.encode("utf-8", "ignore"))


def _candidatos_python():
    import glob
    cands = []
    cfg = _ler_instalacao()
    if cfg.get("python"):
        cands.append(cfg["python"] if isinstance(cfg["python"], list) else [cfg["python"]])
    for v in ("-3.13", "-3.12", "-3.11", "-3"):
        cands.append(["py", v])
    cands.append(["python"])
    roots = [os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramFiles", ""), "C:\\"]
    for r in roots:
        for pat in ("Programs\\Python\\Python3*\\python.exe", "Python3*\\python.exe"):
            for exe in sorted(glob.glob(os.path.join(r, pat)), reverse=True):
                cands.append([exe])
    return cands


def _ler_instalacao():
    p = os.path.join(EXT_ROOT, "config.json")
    if os.path.exists(p):
        try:
            with io.open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def python_cmd():
    """Comando do Python 3.11+ (lista). Procura uma vez e guarda em config.json (fora do Git)."""
    for c in _candidatos_python():
        if _python_ok(c):
            cfg = _ler_instalacao()
            if cfg.get("python") != c:
                cfg["python"] = c
                try:
                    with io.open(os.path.join(EXT_ROOT, "config.json"), "w", encoding="utf-8") as f:
                        f.write(json.dumps(cfg, ensure_ascii=False, indent=1))
                except Exception:
                    pass
            return c
    return None


def dependencias_ok(cmd):
    code, _ = _run(cmd + ["-c", DEPS_IMPORT], env=_env())
    return code == 0


def instalar_dependencias(cmd):
    """pip install --user das bibliotecas do motor (requirements.txt da própria extensão)."""
    req = os.path.join(EXT_ROOT, "requirements.txt")
    return _run(cmd + ["-m", "pip", "install", "--user", "--disable-pip-version-check", "-r", req], env=_env())


def rodar_motor(doc, verificar=False):
    """Extrai, grava raw.json e roda o motor. Retorna (código, verificação, pasta, texto da saída)."""
    py = python_cmd()
    if py is None:
        return -1, None, pasta_saida(doc), "Python 3.11+ não encontrado"
    pasta = pasta_saida(doc)
    if not os.path.isdir(pasta):
        os.makedirs(pasta)
    rawp = os.path.join(pasta, "raw.json")
    with io.open(rawp, "w", encoding="utf-8") as f:
        f.write(json.dumps(extrair_bruto(doc), ensure_ascii=False))
    cmd = py + ["-m", "vigora_frame.cli", "revit", rawp, "--out", pasta]
    cfgp = caminho_config(doc)
    if cfgp and os.path.exists(cfgp):
        cmd += ["--config", cfgp]
    if verificar:
        cmd.append("--verificar")
    code, out = _run(cmd, env=_env())
    if isinstance(out, bytes):
        out = out.decode("utf-8", "ignore")
    return code, ler_verificacao(pasta), pasta, out


def ler_verificacao(pasta):
    ver = os.path.join(pasta, "verificacao.json")
    if not os.path.exists(ver):
        return None
    with io.open(ver, encoding="utf-8") as f:
        return json.load(f)


def linhas_resultado(dados, so_problemas=False):
    """Texto de cada item da verificação (para a lista da janela) + ids do Revit de cada linha."""
    rot = {"error": u"ERRO ", "warning": u"AVISO", "info": u"info "}
    linhas, ids = [], []
    for i in dados.get("issues", []):
        if so_problemas and i["severity"] == "info":
            continue
        txt = u"%s  %s  %s" % (rot.get(i["severity"], u"     "), i["code"], i["message"])
        if i.get("hint"):
            txt += u"\n            -> " + i["hint"]
        linhas.append(txt)
        ids.append(i.get("rids", []))
    return linhas, ids


def resumo_texto(dados):
    s = dados["summary"]
    txt = u"%d erros · %d avisos\n%d painéis · %d peças · %d treliças" % (
        s["errors"], s["warnings"], s["panels"], s["members"], s["trusses"])
    if s.get("pages"):
        txt += u" · %d pranchas" % s["pages"]
    if not s.get("approved"):
        txt += u"\n\nRASCUNHO: regras sem aprovação do engenheiro (não liberar para corte)."
    return txt


def mostrar_elementos(uidoc, rids):
    """Seleciona e dá zoom nos elementos do Revit citados no erro."""
    from System.Collections.Generic import List
    lst = List[DB.ElementId]()
    for n in rids:
        e = uidoc.Document.GetElement(to_eid(n))
        if e is not None:
            lst.Add(e.Id)
    if lst.Count:
        uidoc.Selection.SetElementIds(lst)
        uidoc.ShowElements(lst)
    return lst.Count


# ------------------------------------------------------------------ peças 3D (DirectShape) por diferença
def _solido(s):
    pts = [DB.XYZ(p[0] * MM, p[1] * MM, p[2] * MM) for p in s["profile"]]
    loop = DB.CurveLoop()
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        if a.DistanceTo(b) > 1e-6:
            loop.Append(DB.Line.CreateBound(a, b))
    e = DB.XYZ(s["extrude"][0] * MM, s["extrude"][1] * MM, s["extrude"][2] * MM)
    return DB.GeometryCreationUtilities.CreateExtrusionGeometry([loop], e.Normalize(), e.GetLength())


def aplicar_solidos(doc, dados, log=None):
    """Cria/atualiza DirectShapes. Mantém peças iguais, recria as alteradas, apaga as removidas."""
    existentes = {}
    for ds in DB.FilteredElementCollector(doc).OfClass(DB.DirectShape):
        if ds.ApplicationId == APP_ID:
            existentes[ds.ApplicationDataId] = ds
    novos = dict((s["id"], s) for s in dados["solids"])
    cat = DB.ElementId(DB.BuiltInCategory.OST_GenericModel)
    criados = mantidos = apagados = falhas = 0
    t = DB.Transaction(doc, "Vigora Frame Engine - framing")
    t.Start()
    try:
        for pid, ds in existentes.items():
            s = novos.get(pid)
            com = ds.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            sig = com.AsString() if com is not None else ""
            if s is None or not sig or s["sig"] not in sig:
                doc.Delete(ds.Id)
                apagados += 1
            else:
                mantidos += 1
                novos.pop(pid)
        for pid, s in novos.items():
            try:
                ds = DB.DirectShape.CreateElement(doc, cat)
                ds.ApplicationId = APP_ID
                ds.ApplicationDataId = pid
                ds.SetShape([_solido(s)])
                ds.Name = s["role"]
                ds.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).Set(pid)
                ds.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(
                    "VFE|%s|%s|%s|L=%.0f" % (s["sig"], s["item"], dados["run_id"], s.get("cut_length", 0.0)))
                criados += 1
            except Exception as ex:
                falhas += 1
                if log:
                    log("falha em %s: %s" % (pid, ex))
        t.Commit()
    except Exception:
        t.RollBack()
        raise
    return {"criados": criados, "mantidos": mantidos, "apagados": apagados, "falhas": falhas}


def aplicar_da_pasta(doc, pasta):
    p = os.path.join(pasta, "revit_solidos.json")
    if not os.path.exists(p):
        return None
    with io.open(p, encoding="utf-8") as f:
        return aplicar_solidos(doc, json.load(f))
