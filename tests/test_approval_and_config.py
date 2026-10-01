"""Aprovação (A10.7) e validação do catálogo/ruleset."""
import shutil

import pytest
import yaml

from vigora_frame.builder import run
from vigora_frame.config import Catalog, ConfigError, Rules
from conftest import ROOT, one_wall


def test_default_run_is_draft():
    r = run(one_wall())
    assert r.ruleset_approved is False
    assert any(i.code == "V-000" and "RASCUNHO" in i.message for i in r.issues)


def test_approved_ruleset_releases(tmp_path):
    for d in ("rules", "catalog", "limits"):
        shutil.copytree(ROOT / d, tmp_path / d)
    p = tmp_path / "rules" / "wood-br-v1.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    data["approval"] = {"approved_by": "Eng. Responsável", "registro": "CREA 000", "date": "2026-10-01"}
    for b in data["basis"].values():
        b["approved_by"] = "Eng. Responsável"
    p.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    r = run(one_wall(), root=tmp_path)
    assert r.ruleset_approved is True


def test_unknown_item_raises():
    with pytest.raises(ConfigError):
        Catalog.load().get("NAO-EXISTE")


def test_bad_catalog_item_raises():
    with pytest.raises(ConfigError):
        Catalog._validate_item({"id": "X", "system": "steel", "category": "stud", "web": 0, "flange": 40,
                                "thickness": 0.95, "stock_lengths": [6000]})


def test_unknown_wall_type_raises():
    p = one_wall()
    p.walls[0].wall_type = "ZZ-99"
    with pytest.raises(ConfigError):
        run(p)


def test_system_mismatch_raises():
    p = one_wall()
    p.ruleset = "steel-br-v1"
    with pytest.raises(ConfigError):
        run(p)


def test_header_table_lookup():
    R = Rules.load("wood-br-v1")
    assert R.header_for("cobertura", 1220).item == "W-38x184"
    assert R.header_for("cobertura", 99999) is None
