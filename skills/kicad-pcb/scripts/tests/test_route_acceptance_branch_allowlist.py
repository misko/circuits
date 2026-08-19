from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import route_acceptance_gate as gate  # noqa: E402


def _geometry(branches):
    return {
        "n_seg": 3, "n_via": 1, "n_branch": len(branches),
        "n_cyclic": 0, "n_comp": 1, "n_end": 3,
        "branch_vertices": branches,
    }


def _install(monkeypatch, branches):
    monkeypatch.setattr(
        gate.copper_length_audit, "read_copper",
        lambda _board: ({"USB_P": object()}, ["F.Cu", "B.Cu"], ""))
    monkeypatch.setattr(
        gate.copper_length_audit, "read_plated_pads", lambda _text: {})
    monkeypatch.setattr(
        gate.copper_length_audit, "net_geometry",
        lambda *_args, **_kwargs: _geometry(branches))


def _cfg(at=(28.2, 56.75)):
    return {"route": {"critical_branch_allowlist": [{
        "net": "USB_P", "at": list(at), "layer": "B.Cu", "degree": 3,
        "why": "two reversible connector contacts merge before one path",
    }]}}


def test_exact_critical_branch_is_accepted(monkeypatch):
    _install(monkeypatch, [{
        "x_mm": 28.2, "y_mm": 56.75, "layer": "B.Cu", "degree": 3,
    }])
    result = gate._simple_conductor(
        Path("."), Path("board.kicad_pcb"), ["USB_P"], _cfg())
    assert result["status"] == "PASS"
    assert len(result["nets"][0]["allowed_branch_vertices"]) == 1


def test_moved_branch_and_stale_allowlist_both_fail(monkeypatch):
    _install(monkeypatch, [{
        "x_mm": 28.3, "y_mm": 56.75, "layer": "B.Cu", "degree": 3,
    }])
    result = gate._simple_conductor(
        Path("."), Path("board.kicad_pcb"), ["USB_P"], _cfg())
    assert result["status"] == "FAIL"
    assert any("unapproved branch" in row for row in result["failures"])
    assert any("stale critical_branch_allowlist" in row
               for row in result["failures"])


def test_allowlist_cannot_name_noncritical_net(monkeypatch):
    _install(monkeypatch, [])
    cfg = _cfg()
    cfg["route"]["critical_branch_allowlist"][0]["net"] = "NOT_CRITICAL"
    result = gate._simple_conductor(
        Path("."), Path("board.kicad_pcb"), ["USB_P"], cfg)
    assert result["status"] == "FAIL"
    assert any("non-critical net" in row for row in result["failures"])
