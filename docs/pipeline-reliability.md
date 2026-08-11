# PCB pipeline reliability — bounded execution and evidence lineage

This change carries the useful ideas from the `circuits3` / `meta-skills3`
experiment into the existing pipeline without adopting its agent leases,
epochs, per-directory state machines, or orchestration framework. The unit of
control remains a normal command, project config, generated witness, and test.

## Execution stack

```text
rebuild_all.sh
  -> artifact_provenance begin(pcb_layout, inputs, expected outputs)
  -> schematic/board producer
  -> critical_part_facts(board, accepted facts)       # before route spend
  -> pcb_flow run(stage, timeout)
       -> process_runner.Popen(start_new_session=True)
            -> stream merged stdout/stderr
            -> heartbeat + atomic 06_build state
            -> deadline/cancel => TERM process group => KILL after grace
  -> route prep
  -> route
       -> each wave gets its own bound + state
       -> route_progress.json hashes config, r0 and each rN chain edge
       -> --resume accepts only that authenticated contiguous prefix
       -> a route race has a separate global deadline and cancellation event
  -> import --route-source build|promoted
       -> import_provenance.json hashes selected chain and target before/after
  -> stitch
  -> kicad-cli DRC --severity-all --refill-zones --schematic-parity
  -> artifact_provenance finish(pcb_layout)
  -> project_state(findings.yaml)                     # derived, not asserted
```

The performance budget and hard timeout are deliberately different fields. A
stage can finish successfully but exceed its expected budget; a timeout is an
operator-safety boundary that terminates the whole process group. This follows
Python's documented distinction between subprocess completion and timeout, but
adds group termination because killing only a parent can leave a router or
solver descendant running.

## Evidence stack

```text
accepted sources / design intent
  -> 02_parts/*/part.yaml + 03_src/rules/*.yaml
  -> source producers (TSX, schematic, floorplan, route config)
  -> build provenance (inputs unchanged, outputs written this run)
  -> route lineage (build winner OR reviewed promoted chain)
  -> board + full DRC/parity report
  -> sealed fabrication package
  -> findings.yaml
       DESIGN_CLEAN
         -> FIRST_ARTICLE_ORDERABLE
              -> FIRST_ARTICLE_TESTED
                   -> PRODUCTION_RELEASED
```

An open finding blocks the level named by `blocks_at_or_above`, not every
earlier level. Both boards currently derive `DESIGN_CLEAN`: their prior sealed
releases remain immutable historical evidence, but material pipeline/config
source now differs and therefore requires a fresh canonical rebuild, review
and seal before either current project is called first-article orderable.

## What this changes for the two boards

### USB HUB v3

- Full rebuild explicitly imports the fresh `build` race winner. A leftover
  promoted route or `FINAL` marker is no longer an unstated design decision.
- Six concurrent candidates and every wave have heartbeats and hard bounds.
- J5 is now checked against the accepted order code, exact numbered lands,
  SMD/PTH/NPTH counts, locator drill size, key pad sizes, and key nets before
  routing. This directly targets the wrong-J5-footprint incident class that
  self-consistent schematic/PCB connectivity cannot detect.
- v1.12 remains historical release evidence. Current source is `DESIGN_CLEAN`
  until the bounded pipeline and corrected route-clearance config are rebuilt,
  independently reviewed and sealed; Q9/transient and sustained-load/thermal
  work still blocks `FIRST_ARTICLE_TESTED` after that.

### Pluto RX2 8-way v4

- Canonical rebuild explicitly imports the reviewed `promoted` RF chain. A
  stale build marker cannot silently supersede phase-sensitive copper.
- Existing tscircuit freshness remains the schematic lineage control; the new
  major-stage receipt extends lineage through board generation and final DRC.
- U_SW, the RP2040-Zero module and all ten SMA footprints are checked for
  order-code identity, pad set/count, critical nets, land sizes and drills.
- v1.1 remains historical release evidence. Current source is `DESIGN_CLEAN`
  until the explicit promoted-route lineage and bounded pipeline are rebuilt,
  independently reviewed and sealed; free-running timing, VNA/POFV, rail and
  thermal validation then remain the `FIRST_ARTICLE_TESTED` boundary.

## Negative controls

The implementation is qualified by mutations rather than success-only tests:

- a quiet parent with a sleeping grandchild must time out and lose the whole
  process group;
- a completed artifact is edited after its receipt and audit must fail;
- an order-blocking finding is opened and maturity must fall;
- J5 A5 is resized and the accepted-facts checker must identify that fact;
- a routed `rN` is altered and `--resume` must refuse it;
- both a stale build marker and promoted route exist, and explicit promoted
  selection must win and be recorded.

These tests are in `tests/t1_pipeline_reliability.py` and
`tests/t2_route_stitch.py` and are part of the default suite.

## Standards and tool alignment

- The release DRC invocation matches KiCad's documented full-severity,
  zone-refill and schematic-parity capabilities. KiCad also warns that zones
  must be refilled after track or pad changes before manufacturing output.
- USB-C signal names and receptacle pin identities are anchored to the USB-IF
  Type-C receptacle assignment; the vendor package drawing remains authority
  for J5's physical land and locator geometry.
- Manufacturer documents remain authority for PE42482A-X, RP2040-Zero and SMA
  geometry. The checker records a cited accepted fact; it does not infer a
  footprint from a generic tutorial or from another board.
- IPC/J-STD fabrication and assembly standards remain human/process
  obligations in the release gates. This change does not claim that DRC or a
  passing script substitutes for fabrication notes, first-article inspection,
  electrical test, RF measurement, thermal test, or supplier process control.

Primary references:

- [KiCad 10 command-line DRC documentation](https://docs.kicad.org/10.0/en/cli/cli.html)
- [KiCad PCB Editor DRC and zone guidance](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html)
- [USB Type-C Cable and Connector Specification, release 2.0](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf)
- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)
- [Raspberry Pi hardware design with RP2040](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf)

## Deliberate limits

This is not a distributed workflow engine. It does not schedule agents, claim
work leases, resume arbitrary Python geometry halfway through a pass, update
vendor facts from the network, or promote a release. A timed-out in-process
stitch pass restarts at the stitch boundary; only KRT's explicit wave chain has
authenticated fine-grained resume. Generated state remains disposable under
`06_build`; source decisions remain reviewable YAML and sealed releases remain
immutable.
