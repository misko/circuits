#!/usr/bin/env python3
"""fab_tier_util — resolve a project's declared fab tier into capability floors.

WHY (2026-07-21). The clean-room 3S run (usb-pwr-hub-3s) had to hand-carry
JLC's 4L-standard via floor (0.45/0.3) into route.yaml, the stitch config AND
a bespoke cleanup_vias.py, because nothing derived defaults from the tier the
board had already declared in `03_src/rules/nets.yaml fab_tier:` — the router
emitted 0.6/0.3 hardcoded-default vias on a board whose tier was never
consulted, and the mismatch only surfaced as 2 drill_out_of_range DRC
violations after routing. `references/fab_tiers.yaml` is the SINGLE SOURCE
for these numbers (escape_check / policy_audit already read it for
P-ESC / P-TIER); this helper is how the GENERATORS consume it.

    load_tiers()          -> {name: tier_dict}
    resolve(project_dir)  -> tier dict (with "name" added) or None when the
                             project declares no fab_tier / has no nets.yaml.

A declared fab_tier that fab_tiers.yaml does not know is a HARD ERROR
(FabTierError), never a silent None: a typo'd tier quietly disabling every
capability floor is exactly the failure mode tier-derived defaults exist to
stop (the same discipline as t1_escape_tier's "tier typo" known-bad).

No pcbnew dependency — safe on any python (cmd_route runs on the KRT venv).
"""
from pathlib import Path

import yaml

TIERS_PATH = Path(__file__).resolve().parent.parent / "references" / "fab_tiers.yaml"


class FabTierError(RuntimeError):
    """A declared tier the capability table cannot back. Never caught here."""


def load_tiers(path=TIERS_PATH):
    return yaml.safe_load(Path(path).read_text())["tiers"]


def resolve(project_dir, tiers=None):
    """The tier `<project_dir>/03_src/rules/nets.yaml fab_tier:` declares,
    as a dict with its name injected under "name" — or None if the project
    declares none (legacy behavior stays untouched for those boards)."""
    nets_path = Path(project_dir) / "03_src" / "rules" / "nets.yaml"
    if not nets_path.is_file():
        return None
    name = (yaml.safe_load(nets_path.read_text()) or {}).get("fab_tier")
    if not name:
        return None
    tiers = tiers if tiers is not None else load_tiers()
    if name not in tiers:
        raise FabTierError(
            f"nets.yaml declares fab_tier '{name}' but fab_tiers.yaml only "
            f"knows {sorted(tiers)} — fix the typo, or add the tier WITH "
            f"provenance (canon M6) to {TIERS_PATH}")
    t = dict(tiers[name])
    t["name"] = name
    return t
