# Stage journal — exact parts and interfaces

Date: 2026-08-13

## Objective

Convert the accepted architecture into exact order codes and executable
interface contracts, prove the inexpensive pre-schematic gates, generate no
schematic/PCB artifact, then pause and reflect.

## Execution trace

```text
pipeline(pluto-rx2-8way-v5)
└─ exact_parts_and_interfaces()
   ├─ lock(PE42482A-X, STM32C011F4P6, framed dwell, TPS7A2433)
   ├─ for each exact BOM code (13)
   │  ├─ capture manufacturer document + hash
   │  ├─ extract pins/ratings/package/layout facts
   │  ├─ verify JLC/LCSC identity and dated stock
   │  └─ verify an independent distributor identity
   ├─ prove_interfaces()
   │  ├─ RF truth table + passive ALL_OFF + break-before-make
   │  ├─ timing windows + marker + decoder UNKNOWN behavior
   │  ├─ USB-C Rd/no-data/no-PD boundary
   │  ├─ LDO dropout/current/thermal/effective-capacitance budget
   │  └─ transient clamp vs every exposed downstream rating
   │     └─ FAIL: 10-V C1 < coordinated 10.3-V clamp + margin
   │        ├─ reject C1 exact code
   │        ├─ select/verify 16-V exact code
   │        └─ rerun source + protection gates
   ├─ prove_manufacturing()
   │  ├─ default package tier: 12 parts
   │  ├─ advanced tier: PE42482 0.5-mm QFN
   │  └─ lock JLC04161H-7628 inputs; leave RF width/gap null
   ├─ reconcile(ADRs, BRIEF, architecture, provenance, beacon)
   └─ assert(no TSX, no schematic, no PCB, no fab output)
```

## Result

- 13 exact codes have local dossiers; two document-fetch deviations are
  explicitly recorded rather than hidden.
- All 13 candidate BOM lines had dated JLC catalog stock and independent
  exact-code identity evidence.
- The passive ALL_OFF word, MCU pins, firmware handoff, dwell windows,
  USB-C attach, power budget, protection path, stackup basis and provisional
  RF qualification limits are machine-readable.
- A 10-V input capacitor was rejected and replaced by a 16-V exact code before
  schematic entry.
- No schematic or PCB artifact was generated.

## Where time went

Most effort was deliberate evidence work: extracting exact pin/rating/package
facts, reconciling current manufacturer revisions, checking independent order
codes, and translating prose into executable rule files. The actual JLC stock
query and mechanical source gates completed quickly; none of the checks sat
silently for a long-running generation step. Amphenol's HTTP 403 and ST's local
Rev-4/current-Rev-5 mismatch required bounded deviation records instead of an
unbounded retry loop.

## Stage reflection

Cheap source gates paid for themselves before generation: the surge check
caught a real capacitor-rating error, the escape check confined the advanced
tier to one QFN, and the module-first check demonstrated that the simple MCU
did not justify a radio/module. This stage is a useful reusable boundary:
exact-code and interface closure should happen before TSX, schematic symbols,
footprints, or placement can turn substitutions into rework.

The next stage should generate only the schematic and stop again after cheap
schema validation, ERC, netlist/pin-map parity, and an explicit human
readability review.

## Checkpoint audit correction — 2026-08-13

The first stage account above records what was believed at the original pause;
this append-only correction supersedes its counts and closure claim. The
candidate list initially contained 13 codes because both a rejected 10-V
capacitor and its 16-V replacement remained in the evidence set. The retained
design uses one 16-V 4.7-uF exact code for C1-C3, so the authoritative
candidate BOM and dossier set now contain 12 codes.

The canonical pre-schematic readers then exposed four source-contract defects:
the electrical-invariant file contained prose instead of executable rows; the
RF file did not implement the canonical port/cross-section schema; scalar
`not_assembled` rows caused an assembly-reader traceback; and a misspelled
label-survival shape passed with zero graded rows. Six hard-part dossiers also
stopped their precedent record at a manufacturer artifact without naming the
stronger routed artifact that had not been obtained. These were repaired in
authored source and generic readers before any TSX, schematic or PCB work.

The first composed two-source run failed 3/13 rows and took about 53.1 seconds.
Removing the rejected code, consolidating C1-C3 on the qualified 16-V part,
and recording two current exact DigiKey product-page observations produced a
12/12 pass. The JLC catalog refresh took about 20.8 seconds; a cache-backed
recheck took 0.09 seconds. The complete applicable board-local source battery
took about 1.2 seconds with warm evidence. Focused validator regressions ran
108 tests in about 8.8 seconds.

Final source coverage is recorded in
`source-audit-2026-08-13.md`: 24/24 YAML files parse; 17/17 invariants, 11
label-map rows, 8/8 control states/windows, two RF port groups, one deferred RF
cross-section, four RF claims, 5 declared test-point DNPs, 1/1 module decision,
1/1 power rail, 4/4 early electrical families, 6/6 source net classes, 6/6
hard-part precedent records, 604/604 governed schema keys, 13/13 declared ADR
bound blocks, and 12/12 composed two-source rows pass. The exact checkpoint
pins 50/50 source/evidence files.

The schema ratchet initially found 29 v5 fields with no canonical reader. Most
were duplicate architecture prose or hand-maintained completion flags in
`requirements.yaml`, `integration.yaml`, and pre-PCB sentinel files. They were
removed instead of declared authoritative. Assembly, control-protocol and RF
contracts were then added as governed families, raising the repository floor
from 13 to 16 families and from 424 to 508 proven keys without introducing an
unread claim. The final fleet audit reports 604/604 declared keys, zero orphan
and zero unread.

No source generator was invoked during this correction. There is still no
TSX, circuit JSON, schematic, PCB, route, fabrication or release artifact.
