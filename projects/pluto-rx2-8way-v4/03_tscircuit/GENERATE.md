# Generate v4

From the project root:

```sh
python3 ../../skills/kicad-pcb/scripts/pcb_flow.py preflight .
bash 03_src/rebuild_all.sh
```

The full driver builds TSX, refreshes the human schematic, converts to KiCad,
exports the netlist, runs semantic and power gates, generates placement/rules,
then routes and checks DRC. During first routing there is deliberately no
`route.final`; use the bounded `pcb_flow.py grind`/route race, measure the
winner, promote that exact chain, and only then add `route.final`.

Do not run a bespoke board generator. V4 uses `floorplan.yaml`, `route.yaml`,
the generic backend, and the module-specific footprint/evidence in
`02_parts/RP2040-Zero`.
