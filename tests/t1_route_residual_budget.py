#!/usr/bin/env python3
"""T1: broad A* ground rescue remains visibly bounded."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ROUTER = ROOT / "skills/kicad-pcb/scripts/route_and_stitch_generic.py"
TEMPLATE = ROOT / "skills/pcb-design/templates/03_src/route.yaml"


@test("canonical A-star fallback has residual and time ceilings")
def t_bounded_astar_contract():
    source = ROUTER.read_text()
    template = TEMPLATE.read_text()
    for token in ("max_pending", "budget_s", "A* fallback SKIPPED",
                  "A* budget exhausted", "A* trying"):
        check(token in source, f"router lost bounded A* token {token}")
    check("max_pending: 8" in template and "budget_s: 30" in template,
          "canonical route template lost bounded A* defaults")


@test("unbounded legacy A-star shape is rejected", kind="known_bad")
def t_unbounded_astar_known_bad():
    old = "astar_fallback: {net: GND, width: 0.25, attempts: 3}"
    check("max_pending" not in old and "budget_s" not in old,
          "known-bad unexpectedly contains a bound")


if __name__ == "__main__":
    raise SystemExit(main())
