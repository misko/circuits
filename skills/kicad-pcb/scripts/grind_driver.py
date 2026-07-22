#!/usr/bin/env python3
"""grind_driver — the BOUNDED mechanical DRC grind loop.

WHY (2026-07-21). Measured cost data says the DRC grind loop dominates
board cost: the v4 usb-hub-3s canary's first full DRC on a fresh 112-part
board carried 648 findings, and each grind cycle (rebuild chain + full DRC
+ a frontier agent reading the report) ran ~8-10 minutes / ~500k tokens
per board. Most of that loop is MECHANICAL: classify the findings, look
each class up, rerun a known fix, re-measure. This driver does exactly
that part — and ONLY that part — with hard stop conditions, so the
expensive agent is summoned once with a compact escalation report instead
of once per cycle.

    /usr/bin/python3 grind_driver.py <project-root> [--config 03_src/route.yaml]

ONE CYCLE:
  1. MEASURE. While the routed board is dirty at the `quick` level, iterate
     against `route_and_stitch_generic.py quick` (seconds); once quick is
     clean, the FULL gate (kicad-cli pcb drc --severity-all --refill-zones
     --schematic-parity) is the arbiter. quick is a loop tool, never the
     release gate.
  2. CLASSIFY, never count (the spf 96785a0 lesson): findings become
     {class: count + samples}; clearance-family items are additionally
     split real (cross-net, below the fab floor) vs margin, the
     classified_drc.py approach.
  3. TABLE. Each class is looked up in references/grind_fixes.yaml:
     `action: auto` entries name a conservatively-safe rerun (v1: the
     rebuild chain — all shipped auto fixes live in the generators);
     `action: escalate` and NOVEL classes stop the loop.
  4. JOURNAL (canon M9): one measured entry per cycle appended to
     01_docs/journal/routing.md.

STOP CONDITIONS — the driver is UNABLE to loop forever (an unbounded
auto-fixer is worse than none):
  * full gate 0/0/0 ................................ exit 0
  * a class the table escalates .................... exit 2 + report
  * a NOVEL class with no table entry .............. exit 3 + report
  * D-BACK: 3 consecutive cycles without total-count
    improvement, or the --max-cycles cap ........... exit 4 + report
  * config / infrastructure error .................. exit 1
The escalation report is 06_build/grind_escalation.md: per class — count,
sample items, and WHY there is no auto-fix.

TEST SEAMS (hermetic, the stub_krt pattern): --check-cmd replaces the
measurement with a shell command that writes a gate.json-format file to
the path substituted for {out}; --rebuild-cmd replaces the auto-fix chain.
"""
import argparse
import datetime
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                          # pragma: no cover
    sys.exit("grind_driver needs pyyaml")

SCRIPTS = Path(__file__).resolve().parent
FIXES_DEFAULT = SCRIPTS.parent / "references" / "grind_fixes.yaml"
KPY = "/usr/bin/python3"
EXIT_CLEAN, EXIT_INFRA, EXIT_ESCALATE, EXIT_NOVEL, EXIT_DBACK = 0, 1, 2, 3, 4


def load_fixes(path):
    d = yaml.safe_load(Path(path).read_text()) or {}
    table = {}
    for e in d.get("fixes") or []:
        if not e.get("class") or e.get("action") not in ("auto", "escalate"):
            sys.exit(f"grind_driver: bad grind_fixes entry {e!r} — need "
                     f"class + action auto|escalate")
        table[e["class"]] = e
    if not table:
        sys.exit(f"grind_driver: {path} defines no fixes")
    return table


# ------------------------------------------------------------ classify --
def classify_gate(g, fab_floor=0.10):
    """gate.json -> {class: {count, samples[]}} — CLASSIFIED, never a bare
    count. clearance-family items get the classified_drc real/margin split
    in their samples so the escalation report says which are fab-real."""
    out = {}

    def add(cls, desc):
        e = out.setdefault(cls, {"count": 0, "samples": []})
        e["count"] += 1
        if len(e["samples"]) < 3 and desc:
            e["samples"].append(desc[:160])

    for v in g.get("violations", []):
        cls, desc = v.get("type", "?"), v.get("description", "")
        if cls in ("clearance", "hole_clearance"):
            m = re.search(r"actual ([0-9.]+) mm", desc)
            val = float(m.group(1)) if m else -1.0
            nets = set()
            for it in v.get("items", []):
                mm2 = re.search(r"\[([^\]]+)\]", it.get("description", ""))
                if mm2:
                    nets.add(mm2.group(1))
            tag = ("REAL" if len(nets) > 1 and 0 <= val < fab_floor
                   else "margin" if len(nets) > 1 else "same-net")
            desc = f"[{tag}] {desc}"
        add(cls, desc)
    for u in g.get("unconnected_items", []):
        add("unconnected",
            " <-> ".join(i.get("description", "")
                         for i in u.get("items", []))[:160])
    for p in g.get("schematic_parity", []):
        add("schematic_parity", p.get("description", ""))
    return out


def total_of(findings):
    return sum(e["count"] for e in findings.values())


# ------------------------------------------------------------- measure --
def run_check_cmd(cmd, root, out_path):
    real = cmd.replace("{out}", str(out_path))
    r = subprocess.run(real, shell=True, cwd=str(root),
                       capture_output=True, text=True)
    if not out_path.is_file():
        sys.exit(f"grind_driver: --check-cmd wrote no {out_path} "
                 f"(exit {r.returncode}): {(r.stderr or r.stdout)[-400:]}")
    return json.loads(out_path.read_text())


def measure(args, root, cfg_path, board):
    """-> (mode, findings). quick while dirty, full once quick is clean."""
    scratch = root / "06_build" / "grind"
    scratch.mkdir(parents=True, exist_ok=True)
    if args.check_cmd:
        g = run_check_cmd(args.check_cmd, root, scratch / "check.json")
        return "check-cmd", classify_gate(g, args.fab_floor)
    qjson = scratch / "quick.json"
    rq = subprocess.run([KPY, str(SCRIPTS / "route_and_stitch_generic.py"),
                         "quick", str(cfg_path), "--json", str(qjson)],
                        cwd=str(root), capture_output=True, text=True)
    if not qjson.is_file():
        sys.exit(f"grind_driver: quick produced no JSON (exit "
                 f"{rq.returncode}): {(rq.stderr or rq.stdout)[-400:]}")
    q = json.loads(qjson.read_text())
    if q["verdict"] == "DIRTY":
        findings = {}
        for cls, e in q.get("violations", {}).items():
            findings[cls] = {"count": e["count"],
                             "samples": list(e.get("samples", []))[:3]}
        ru = q["unconnected"]
        if ru["routed_total"]:
            findings["unconnected"] = {
                "count": ru["routed_total"],
                "samples": [f"{n} x{c}"
                            for n, c in list(ru["routed"].items())[:3]]}
        return "quick", findings
    gj = scratch / "gate.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all",
                    "--refill-zones", "--schematic-parity", "--format",
                    "json", "-o", str(gj), str(board)],
                   cwd=str(root), capture_output=True, text=True)
    if not gj.is_file():
        sys.exit("grind_driver: full DRC wrote no gate.json")
    return "full", classify_gate(json.loads(gj.read_text()), args.fab_floor)


# --------------------------------------------------------------- output --
def journal(root, n, mode, findings, best, stall, action):
    p = root / "01_docs" / "journal" / "routing.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    counts = ", ".join(f"{k}={e['count']}"
                       for k, e in sorted(findings.items())) or "none"
    entry = (f"\n## {ts} — iterate {n} (grind)\n"
             f"- did: grind cycle {n}: measure({mode}) -> {action}\n"
             f"- result: total {total_of(findings)} findings — {counts} "
             f"(best {best}, stalled {stall}/3)\n"
             f"- next: {'done' if not findings else action}\n")
    with p.open("a") as f:
        f.write(entry)


def write_escalation(root, reason, findings, table, history):
    p = root / "06_build" / "grind_escalation.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# grind escalation — {ts}", "",
             f"**Reason: {reason}**", "",
             "Totals per cycle: " + " -> ".join(str(t) for t in history), ""]
    for cls, e in sorted(findings.items()):
        t = table.get(cls)
        if t is None:
            why = "NOVEL CLASS — no grind_fixes.yaml entry; a driver that " \
                  "guessed here would be an unbounded auto-fixer"
        elif t["action"] == "escalate":
            why = str(t.get("why", "table says escalate")).strip()
        else:
            why = (f"action=auto ({t.get('run')}) but the loop stopped: "
                   f"{reason}")
        lines += [f"## {cls} — {e['count']}",
                  f"- why no auto-fix: {why}"]
        lines += [f"- sample: {s}" for s in e["samples"]]
        lines += [""]
    lines += ["Next: the D-BACK ladder (skills/pcb-design/SKILL.md) maps "
              "each class to the stage that owns it. Re-run grind_driver "
              "after the design change."]
    p.write_text("\n".join(lines) + "\n")
    print(f"escalation report -> {p}")


# ------------------------------------------------------------------ main --
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--config", default="03_src/route.yaml")
    ap.add_argument("--fixes", default=str(FIXES_DEFAULT))
    ap.add_argument("--max-cycles", type=int, default=12,
                    help="hard cap regardless of progress (default 12)")
    ap.add_argument("--fab-floor", type=float, default=0.10)
    ap.add_argument("--check-cmd", default=None,
                    help="TEST SEAM: shell command writing gate.json-format "
                         "findings to {out}, replacing quick/full measurement")
    ap.add_argument("--rebuild-cmd", default=None,
                    help="auto-fix chain override (default: bash "
                         "03_src/rebuild_all.sh)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    cfg_path = root / args.config
    board = None
    if cfg_path.is_file():
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
        b = (cfg.get("project") or {}).get("board")
        board = (root / b) if b else None
    elif not args.check_cmd:
        sys.exit(f"grind_driver: no {cfg_path} and no --check-cmd")
    table = load_fixes(args.fixes)
    rebuild_cmd = args.rebuild_cmd or "bash 03_src/rebuild_all.sh"
    if args.max_cycles < 1:
        sys.exit("grind_driver: --max-cycles must be >= 1")

    best, stall, history = None, 0, []
    for n in range(1, args.max_cycles + 1):
        mode, findings = measure(args, root, cfg_path, board)
        total = total_of(findings)
        history.append(total)
        # D-BACK bookkeeping BEFORE any fix: 3 consecutive measurements
        # with no NEW BEST total = stagnation, stop. The baseline cycle
        # counts as "no improvement yet", so a board whose findings never
        # move terminates on cycle 3, not 4 — the bound the known-bad
        # fixture pins.
        if best is None:
            best, stall = total, 1
        elif total < best:
            best, stall = total, 0
        else:
            stall += 1
        print(f"cycle {n} [{mode}]: {total} findings — "
              + (", ".join(f"{k}={e['count']}"
                           for k, e in sorted(findings.items())) or "none"))

        if not findings:
            # only reachable in full / check-cmd mode: a DIRTY quick always
            # carries findings, and a clean quick hands over to the full gate
            journal(root, n, mode, findings, best, stall, "clean, done")
            print("grind: 0/0/0 — done")
            return EXIT_CLEAN

        novel = sorted(c for c in findings if c not in table)
        esc = sorted(c for c in findings
                     if c in table and table[c]["action"] == "escalate")
        autos = sorted(c for c in findings
                       if c in table and table[c]["action"] == "auto")

        if novel:
            journal(root, n, mode, findings, best, stall,
                    f"ESCALATE novel class {novel}")
            write_escalation(root, f"novel class(es) {novel} — no table "
                                   f"entry", findings, table, history)
            return EXIT_NOVEL
        if stall >= 3:
            journal(root, n, mode, findings, best, stall,
                    "ESCALATE D-BACK stagnation")
            write_escalation(root, "D-BACK: 3 consecutive cycles without "
                                   "total-count improvement",
                             findings, table, history)
            return EXIT_DBACK
        if not autos:
            journal(root, n, mode, findings, best, stall,
                    f"ESCALATE table classes {esc}")
            write_escalation(root, f"table-escalated class(es) {esc}",
                             findings, table, history)
            return EXIT_ESCALATE

        # conservatively-safe auto fixes: v1 = the rebuild chain rerun
        runs = sorted({table[c].get("run", "rebuild") for c in autos})
        if runs != ["rebuild"]:
            journal(root, n, mode, findings, best, stall,
                    f"ESCALATE unknown auto procedure {runs}")
            write_escalation(root, f"auto entries name unknown "
                                   f"procedure(s) {runs}", findings, table,
                             history)
            return EXIT_ESCALATE
        print(f"  auto-fix ({', '.join(autos)}): {rebuild_cmd}")
        r = subprocess.run(rebuild_cmd, shell=True, cwd=str(root),
                           capture_output=True, text=True)
        journal(root, n, mode, findings, best, stall,
                f"auto-fix rebuild for {autos} (exit {r.returncode})")
        if r.returncode != 0:
            write_escalation(root, f"auto-fix chain exited "
                                   f"{r.returncode}", findings, table,
                             history)
            return EXIT_ESCALATE

    write_escalation(root, f"--max-cycles cap ({args.max_cycles}) reached",
                     findings, table, history)
    return EXIT_DBACK


if __name__ == "__main__":
    sys.exit(main())
