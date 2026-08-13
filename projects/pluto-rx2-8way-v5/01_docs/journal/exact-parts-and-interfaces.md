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
