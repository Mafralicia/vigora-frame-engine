"""Gera os arquivos golden a partir da versão atual (rodar só quando a mudança for intencional)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vigora_frame.builder import load_project, run
from vigora_frame.config import Catalog, Rules
from vigora_frame.quantities import quantities


NAMES = sorted(p.stem for p in (ROOT / "examples").glob("*.json"))


def snapshot(name):
    p = load_project(ROOT / "examples" / f"{name}.json")
    r = run(p)
    q = quantities(r, Catalog.load(), Rules.load(p.ruleset))
    return {"panels": r.stats["panels"], "members": r.stats["members"], "connections": r.stats["connections"],
            "sheets": r.stats["sheets"], "trusses": r.stats["trusses"], "members_by_role": r.stats["members_by_role"],
            "errors": r.stats["issues"].get("error", 0), "quantities": q["summary"], "run_id": r.run_id}


if __name__ == "__main__":
    for n in NAMES:
        (ROOT / "tests" / "golden" / f"{n}.json").write_text(json.dumps(snapshot(n), indent=1), encoding="utf-8")
        print("golden", n)
