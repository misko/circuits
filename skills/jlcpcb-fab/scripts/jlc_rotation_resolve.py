"""Shared JLC CPL-rotation resolution for the exporter and the twin.

JLC's zero-orientation is a PER-LCSC fact — it is how JLC drew that specific
component's footprint in its own library, and two different parts that share a
KiCad footprint NAME can carry different zero-orientations. Measured on this
fleet (2026-07-24): C79924 and C7719 are both `SOT-23-5`, yet the exact
pad-fit needs offset 180 for C79924 and 90 for C7719. A footprint-NAME-keyed
table (`jlc_rotations_db.csv`) physically cannot encode that — the name key IS
the bug. So a per-LCSC table (`jlc_lcsc_rotations.csv`, keyed `LCSC,rotation,
evidence`) is consulted FIRST and wins over the name DB; a part with no
per-LCSC row falls through to the name DB unchanged (existing behaviour is
preserved for every un-overridden part).

No pcbnew dependency: the exporter (`export_jlc_package.py`) and the twin
(`jlc_twin.py`) both import this, and it is unit-testable with plain python3.
"""
import csv
from pathlib import Path

LCSC_ROT_PATH = Path(__file__).parent / "jlc_lcsc_rotations.csv"


def load_lcsc_rotations(path=None):
    """Return {LCSC: offset_deg} from the per-LCSC rotation table.

    Populate ONLY with codes whose exact pad-fit was MEASURED by the twin
    (cite the fit in the `evidence` column). A guessed row is worse than none:
    it silently overrides the name DB fleet-wide.
    """
    table = {}
    p = Path(path) if path else LCSC_ROT_PATH
    if p.exists():
        with open(p) as f:
            for row in csv.DictReader(f):
                code = (row.get("LCSC") or "").strip()
                rot = (row.get("rotation") or "").strip()
                if code and rot and not code.startswith("#"):
                    try:
                        table[code] = float(rot)
                    except ValueError:
                        pass
    return table


def resolve_rotation(fpname, board_rot, lcsc, name_db, lcsc_table):
    """Resolve the JLC CPL rotation for one part.

    Returns (cpl_rotation, offset, source) where source is one of
    "lcsc" | "name" | "none". CPL rotation = (board_rot + offset) % 360.

    - `name_db`   : list of (compiled_regex, offset) — the footprint-NAME DB.
    - `lcsc_table`: {LCSC: offset} — the per-LCSC overrides (WIN over name_db).

    Per-LCSC is checked first because JLC's zero-orientation is a per-part
    fact; two parts sharing a footprint name may need different offsets.
    """
    if lcsc and lcsc in lcsc_table:
        off = lcsc_table[lcsc]
        return round((board_rot + off) % 360, 1), off, "lcsc"
    for pat, off in name_db:
        if pat.search(fpname):
            return round((board_rot + off) % 360, 1), off, "name"
    return round(board_rot % 360, 1), 0.0, "none"
