# GENERATE — pluto-rx2-8way `03_tscircuit/`

## The schematic gate (this stage) — one command

```
export PATH="$HOME/.bun/bin:$PATH"
/usr/bin/python3 ../../../skills/kicad-pcb/scripts/tsx_preflight.py ..   # BEFORE the first build
bash ../../../skills/kicad-pcb/scripts/gen_tscircuit.sh ..
```

`tsx_preflight.py` FIRST is not a style preference. `J_USB`'s pads are
`A1..B12` + `SH`, and tscircuit rejects alphanumeric pad ids **without failing
the build** — the part vanishes and ERC still reads 0 errors. Run it before
`tsci build`, not after, because the failure is a MISSING part and a missing
part is exactly what count-parity exists to catch.

`gen_tscircuit.sh` (no flag) emits the BRIDGE ONLY and writes nothing outside
`03_tscircuit/`:

| artifact | audience |
|---|---|
| `build/circuit.json` | both — the single source the two audiences compile from |
| `build/schematic.svg` / `.pdf` | **humans**; the release ships the PDF |
| `kicad/pluto_rx2_8way.kicad_sch` | **the machine** — ERC / netlist / parity / backend |
| `verification/erc_converter.rpt` | the gate: `kicad-cli sch erc --severity-all` = 0 errors |

`--study` adds tscircuit's own PCB/gerbers/3D. Never a fab source (ADR-0002's
two hard lines: KRT owns routing physics, `jlc_twin` owns the independent
referee), and off by default.

## Then the cheap semantic battery, at THIS gate and not first at seal

A defect authored here and caught at seal costs a superseded release.

```
S=../../../skills/kicad-pcb/scripts;  F=../../../skills/jlcpcb-fab/scripts
/usr/bin/python3 $S/count_parity.py ..                    # S-COUNT
/usr/bin/python3 $S/net_label_survival.py ..              # S-NETMERGE
/usr/bin/python3 $S/electrical_invariants.py ..           # E-INV
/usr/bin/python3 $S/electrical_invariants.py .. --adr-coverage   # E-ADR
/usr/bin/python3 $S/power_topology.py ..                  # E-TOPO
/usr/bin/python3 $S/power_topology.py .. --margin         # E-MARGIN
/usr/bin/python3 $S/power_topology.py .. --off-control    # E-OFF
/usr/bin/python3 $F/bom_source_check.py --circuit-only build/circuit.json --parts ../02_parts
/usr/bin/python3 $S/policy_audit.py ..
```

**Read `net_label_survival`'s COUNT, not just its exit code.** A sibling board's
rebuild silently MERGED `3V3_ANALOG` into `3V3` — a wire root carrying two
different label names — and would have undone a shipped fix; it was caught only
because the count came back 161/162. The converter has since been patched. The
count is still the evidence.

## The whole board (stage 5-6, not yet)

```
bash ../03_src/rebuild_all.sh        # full: tsci -> converter -> board -> route -> DRC
bash ../03_src/rebuild_reuse.sh      # per-iteration: skips tsci, replays the promoted chain
```

`rebuild_reuse.sh` consumes the COMMITTED `kicad/pluto_rx2_8way.kicad_sch` as
the PINNED canonical schematic, because **`tsci build` is NON-DETERMINISTIC**:
rerunning it churns ~2900 lines of UUID/ordering noise and `kicad-cli
--schematic-parity` then reports phantom field diffs. Rerun `tsci` only when the
TSX changed, then re-commit the `.kicad_sch` as the new pin.

Neither driver can run to completion yet: `03_src/route.yaml` deliberately
carries no `final:` key because no KRT chain has been promoted into
`03_src/route/`. Its absence is what makes `import` a no-op rather than a
silent wrong replay.
