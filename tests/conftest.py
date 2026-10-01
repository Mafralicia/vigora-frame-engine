import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vigora_frame.model import Project  # noqa: E402


def one_wall(system="wood", length=6000, openings=(), exterior=True, bearing=True, height=2700):
    return Project.model_validate({
        "id": "T", "name": "teste", "system": system,
        "ruleset": "wood-br-v1" if system == "wood" else "steel-br-v1",
        "levels": [{"id": "L1", "name": "T", "elevation": 0, "height": height}],
        "walls": [{"id": "W1", "level": "L1", "start": [0, 0], "end": [length, 0], "height": height,
                   "exterior": exterior, "bearing": bearing, "openings": list(openings)}],
    })


def errors(res, ignore=("V-017",)):
    return [i for i in res.issues if i.severity == "error" and i.code not in ignore]


@pytest.fixture(scope="session")
def examples_dir():
    return ROOT / "examples"
