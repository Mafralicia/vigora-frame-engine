"""Steel frame: alinhamento em linha (V-004) e comprimentos em guia."""
import pytest

from vigora_frame.builder import load_project, run


@pytest.fixture(scope="module")
def steel(examples_dir):
    return run(load_project(examples_dir / "casa_terrea_steel.json"))


def test_in_line_checked_and_ok(steel):
    info = next(i for i in steel.issues if i.element == "in-line")
    checked = int(info.message.split()[0])
    assert checked >= 20
    assert not any(i.code == "V-004" for i in steel.issues)


def test_stud_length_inside_tracks(steel):
    st = next(m for m in steel.members if m.role == "STUD" and m.item.startswith("LSF-UE-140"))
    assert st.cut_length == pytest.approx(2700 - 2 * 0.95 - 3, abs=0.1)


def test_x_bracing_angles(steel):
    straps = [m for m in steel.members if m.role == "BRACE_STRAP"]
    assert straps
    for m in straps:
        ang = float(m.note.split(" a ")[1].rstrip("°"))
        assert 30 <= ang <= 60


def test_panels_within_steel_limit(steel):
    assert all(p.length <= 6000 for p in steel.panels)
