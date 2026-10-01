"""Golden: os exemplos têm que produzir exatamente o mesmo resultado (regressão)."""
import json

import pytest

from conftest import ROOT
from make_golden import NAMES, snapshot


@pytest.mark.parametrize("name", NAMES)
def test_golden(name):
    exp = json.loads((ROOT / "tests" / "golden" / f"{name}.json").read_text(encoding="utf-8"))
    got = snapshot(name)
    assert got == exp
