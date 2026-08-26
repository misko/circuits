# Generate — pluto-cal-switch

Board internal name: `pluto_cal_switch`.
Authoring file: `src/pluto_cal_switch.tsx`.
This board writes **ZERO board-specific generation Python** — everything below
is a SHARED skill script driven by `03_src/*.yaml` (ADR-0002 amendment).

```bash
export PATH="$HOME/.bun/bin:$PATH"
S=~/.claude/skills/kicad-pcb/scripts     # or <repo>/skills/kicad-pcb/scripts

# 0. TSX-PRE preflight — RUN THIS BEFORE THE FIRST `tsci build`.
#    tscircuit DROPS a part with alphanumeric pads SILENTLY and ERC still
#    reads 0. This is not optional and it is not re-orderable.
python3 $S/tsx_preflight.py projects/pluto-cal-switch

# 1. the schematic bridge (default = BRIDGE ONLY): circuit.json,
#    build/schematic.pdf (THE HUMAN DOCUMENT), kicad/pluto_cal_switch.kicad_sch
#    (the machine artifact), + ERC and netlist parity
bash $S/gen_tscircuit.sh projects/pluto-cal-switch

# 2. refdes SET parity: the hand-authored manifest.yaml vs EVERY generated
#    artifact. Generated artifacts all agree with each other after a silent
#    drop; only declared intent disagrees.
python3 $S/count_parity.py projects/pluto-cal-switch

# 3. the CHEAP SEMANTIC BATTERY — at the SCHEMATIC gate, not at seal.
#    A defect authored here and caught at seal costs a superseded release.
python3 $S/net_label_survival.py   projects/pluto-cal-switch     # S-NETMERGE
python3 $S/electrical_invariants.py projects/pluto-cal-switch    # E-INV
python3 $S/electrical_invariants.py projects/pluto-cal-switch --adr-coverage
python3 $S/power_topology.py projects/pluto-cal-switch           # E-TOPO
python3 $S/power_topology.py projects/pluto-cal-switch --margin  # E-MARGIN
python3 $S/power_topology.py projects/pluto-cal-switch --off-control  # E-OFF
python3 ~/.claude/skills/jlcpcb-fab/scripts/bom_source_check.py --circuit-only \
        projects/pluto-cal-switch/03_tscircuit/build/circuit.json \
        --parts projects/pluto-cal-switch/02_parts

# 4. the WHOLE board (stage 5-6, NOT YET AUTHORED — 03_src/floorplan.yaml
#    carries no placement and 03_src/route/ carries no promoted chain):
bash projects/pluto-cal-switch/03_src/rebuild_all.sh
```

**`tsci build` is NON-DETERMINISTIC** — rerunning it churns the generated
`.kicad_sch` by thousands of lines of UUID/ordering noise even when
connectivity is unchanged. The COMMITTED `kicad/pluto_cal_switch.kicad_sch` is
therefore the PINNED canonical schematic: per-iteration board rebuilds consume
it via `03_src/rebuild_reuse.sh` and never regenerate it. Only rerun `tsci`
when the TSX actually changed, then re-commit the sch as the new pin.
