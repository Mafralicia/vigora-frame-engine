"""Linha de comando.

  vigora-frame run examples/casa_terrea_wood.json --out out/casa
  vigora-frame diff out/v1/resultado.json out/v2/resultado.json
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import typer

from .builder import load_project, load_result, run, save_result
from .config import Catalog, Rules
from .diff import diff as diff_results
from .export.drawings import write_drawings
from .export.pranchas_nbr import write_pranchas
from .export.factory import write_csv, write_dxf, write_labels
from .export.xlsx import write_xlsx
from .quantities import quantities
from .revit_bridge import revit_solids

app = typer.Typer(add_completion=False, help="Vigora Frame Engine")


def export_all(project_path: str, out: str, drawings: bool = True, formato: str = "A1") -> dict:
    t0 = time.time()
    out_p = Path(out)
    out_p.mkdir(parents=True, exist_ok=True)
    proj = load_project(project_path)
    res = run(proj)
    from .clash import add_clash_issues
    add_clash_issues(res)                       # toda peça contra toda peça, em 3D
    t_engine = time.time() - t0
    cat = Catalog.load()
    rules = Rules.load(proj.ruleset)
    q = quantities(res, cat, rules)
    save_result(res, out_p / "resultado.json")
    write_xlsx(res, q, cat, str(out_p / "quantitativo.xlsx"))
    files = write_csv(res, q, str(out_p))
    write_dxf(res, str(out_p / "paineis_e_trelicas.dxf"))
    write_labels(res, str(out_p / "etiquetas_paineis.pdf"), str(out_p / "etiquetas_pecas.zpl"))
    (out_p / "revit_solidos.json").write_text(json.dumps(revit_solids(res)), encoding="utf-8")
    pages = 0
    if drawings:
        pages = write_pranchas(res, q, str(out_p / f"pranchas_{formato}.pdf"), fmt=formato,
                               levels=[lv.model_dump() for lv in proj.levels])
        write_drawings(res, q, str(out_p / "pranchas_rapidas_A3.pdf"))
    summary = {"project": res.project, "run_id": res.run_id, "approved": res.ruleset_approved,
               "engine_seconds": round(t_engine, 2), "total_seconds": round(time.time() - t0, 2),
               "pages": pages, **{k: v for k, v in res.stats.items() if k not in ("placements", "levels", "members_by_role")},
               "quantities": q["summary"]}
    (out_p / "resumo.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    return summary


@app.command("run")
def run_cmd(project: str, out: str = typer.Option("out", help="pasta de saída"),
            no_drawings: bool = typer.Option(False, help="pula as pranchas"),
            formato: str = typer.Option("A1", help="formato das pranchas NBR: A1 ou A0")):
    s = export_all(project, out, drawings=not no_drawings, formato=formato.upper())
    typer.echo(json.dumps(s, indent=1, ensure_ascii=False))
    if s["issues"].get("error", 0):
        raise typer.Exit(code=2)


@app.command("diff")
def diff_cmd(old: str, new: str):
    d = diff_results(load_result(old), load_result(new))
    typer.echo(f"adicionadas {len(d['added'])} · removidas {len(d['removed'])} · alteradas {len(d['changed'])} · "
               f"sem mudança {d['unchanged']}")
    typer.echo("painéis alterados: " + ", ".join(d["panels_changed"]))




# ------------------------------------------------------------------ caixa d'água (adicionar/mover/trocar/remover)
tank_app = typer.Typer(help="Caixa d'água no ático: o entorno (vigas, deck, treliças de ático) é refeito sozinho.")
app.add_typer(tank_app, name="caixa")


def _tank_edit(project: str, change):
    """Aplica a mudança no JSON do projeto, gera antes/depois e mostra o que mudou no modelo."""
    path = Path(project)
    before = run(load_project(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("tanks", [])
    msg = change(data)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    after = run(load_project(path))
    d = diff_results(before, after)
    typer.echo(msg)
    typer.echo(f"modelo: +{len(d['added'])} peças · -{len(d['removed'])} · {len(d['changed'])} alteradas")
    marks_b = {t.mark for t in before.trusses}
    marks_a = {t.mark for t in after.trusses}
    if marks_a != marks_b:
        typer.echo(f"treliças: {', '.join(sorted(marks_b))} -> {', '.join(sorted(marks_a))}")
    for i in after.issues:
        if i.code in ("V-090", "V-091", "V-092", "V-093", "V-094") or ("caixa" in i.message and i.code == "V-000"):
            typer.echo(f"  {i.code} {i.severity}: {i.message}")
    errs = after.stats["issues"].get("error", 0)
    typer.echo(f"erros: {errs}")
    raise typer.Exit(1 if errs else 0)


@tank_app.command("adicionar")
def tank_add(project: str, id: str = "CX1", modelo: str = "BR_1000L", nivel: str = "L1",
             x: float = typer.Option(None, help="centro X (vazio = posição automática)"), y: float = None):
    def ch(data):
        data["tanks"] = [t for t in data["tanks"] if t["id"] != id]
        t = {"id": id, "model": modelo, "level": nivel}
        if x is not None and y is not None:
            t["position"] = [x, y]
        data["tanks"].append(t)
        return f"caixa {id} ({modelo}) adicionada " + (f"em ({x:.0f}, {y:.0f})" if x is not None else "(posição automática)")
    _tank_edit(project, ch)


@tank_app.command("mover")
def tank_move(project: str, id: str = "CX1", x: float = typer.Option(None), y: float = typer.Option(None),
              auto: bool = typer.Option(False, help="volta para a posição automática")):
    def ch(data):
        t = next(t for t in data["tanks"] if t["id"] == id)
        if auto:
            t.pop("position", None)
            return f"caixa {id} -> posição automática"
        t["position"] = [x, y]
        return f"caixa {id} movida para ({x:.0f}, {y:.0f})"
    _tank_edit(project, ch)


@tank_app.command("trocar")
def tank_swap(project: str, modelo: str, id: str = "CX1"):
    def ch(data):
        t = next(t for t in data["tanks"] if t["id"] == id)
        old = t["model"]
        t["model"] = modelo
        return f"caixa {id}: {old} -> {modelo}"
    _tank_edit(project, ch)


@tank_app.command("remover")
def tank_remove(project: str, id: str = "CX1"):
    def ch(data):
        data["tanks"] = [t for t in data["tanks"] if t["id"] != id]
        return f"caixa {id} removida"
    _tank_edit(project, ch)


# ------------------------------------------------------------------ ponte com o plugin do Revit
@app.command("revit")
def revit_cmd(raw: str, config: str = typer.Option("", help="configuração do projeto (<modelo>.vigora.json)"),
              out: str = typer.Option("out/revit", help="pasta de saída"),
              verificar: bool = typer.Option(False, help="só verifica (rápido): não gera 3D nem pranchas")):
    """Chamado pelo plugin: dados brutos do Revit + configuração -> projeto, verificações e saídas."""
    from .revit_import import issues_for_revit, normalize
    out_p = Path(out)
    out_p.mkdir(parents=True, exist_ok=True)
    rawd = json.loads(Path(raw).read_text(encoding="utf-8"))
    cfg = json.loads(Path(config).read_text(encoding="utf-8")) if config and Path(config).exists() else {}
    proj, notes = normalize(rawd, cfg)
    (out_p / "projeto.json").write_text(proj.model_dump_json(indent=1), encoding="utf-8")
    if verificar:
        res = run(proj)
        from .clash import add_clash_issues
        add_clash_issues(res)
        pages = 0
    else:
        s = export_all(str(out_p / "projeto.json"), str(out_p), drawings=cfg.get("pranchas", True),
                       formato=cfg.get("formato", "A1"))
        res = load_result(out_p / "resultado.json")
        pages = s["pages"]
    iss = issues_for_revit(res, notes)
    summary = {"errors": sum(1 for i in iss if i["severity"] == "error"),
               "warnings": sum(1 for i in iss if i["severity"] == "warning"),
               "panels": res.stats["panels"], "members": res.stats["members"], "trusses": res.stats["trusses"],
               "pages": pages, "run_id": res.run_id, "approved": res.ruleset_approved}
    (out_p / "verificacao.json").write_text(json.dumps({"summary": summary, "issues": iss}, ensure_ascii=False,
                                                       indent=1), encoding="utf-8")
    typer.echo(json.dumps(summary, ensure_ascii=False))
    raise typer.Exit(2 if summary["errors"] else 0)


if __name__ == "__main__":
    app()
