# Parity — cooksense v1.7

Every number here was measured by the sealing agent on 2026-07-30, UNPIPED,
against the artifacts in THIS archive (and the byte-identical `04_kicad/` copies
they were exported from). Raw exit codes are quoted, not summarised.

## 1. Schematic <-> board parity — the DRC's own third half

    $ cd source
    $ kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
          --format json -o drc.json cooksense.kicad_pcb ; echo "RAW_EXIT=$?"
    Found 0 violations
    Found 0 unconnected items
    Found 0 schematic parity issues
    RAW_EXIT=0

**All three halves are zero.** The unconnected half is quoted here explicitly
because it is the one that historically gets summarised instead of classified
(canon: CLASSIFY, NEVER COUNT — and there is nothing to classify at zero). The
parity half is what catches a part that exists in the schematic and never
reached the board; it is the check KiCad 7 could not make at all.

This exact command was ALSO run on a copy of `source/` extracted to a directory
**outside the repository**, with the same result and the same `RAW_EXIT=0` — see
`build_gates.md`, "Archive self-containment". `drc_standalone.json` in this
directory is that run's report.

## 2. Component-count parity across four independent source pairs (S-COUNT)

    $ count_parity.py projects/smc0985-cooksense --board cooksense ; echo "RAW_EXIT=$?"
    ok   board == manifest        (239/239 components)
    ok   circuit.json == manifest (239/239 components)
    ok   kicad_sch == manifest    (239/239 components)
    ok   netlist == manifest      (239/239 components)
    S-COUNT PASS: 4/4 source pair(s) agree with manifest over 239 refdes
    RAW_EXIT=0

The DECLARED refdes list (`03_tscircuit/manifest.yaml`) is the reference every
generated artifact is compared against — not one artifact compared to another.
That asymmetry is the point: `tsci` drops parts SILENTLY, and generated
artifacts that agree with each other after a silent drop are all wrong together.
Only declared intent can disagree.

`--board cooksense` is REQUIRED on this project and was supplied. Run without
it, `count_parity.py` **refuses** (`2 kicad_sch artifacts and no --board:
['cooksense', 'interposer']`) rather than silently grading one of two boards —
verified this pass, raw exit 1.

## 3. Board / archive identity

    04_kicad/cooksense.kicad_pcb   md5 9f4fd5fae810f40a52b1035df727243c
    source/cooksense.kicad_pcb     md5 9f4fd5fae810f40a52b1035df727243c   IDENTICAL
    04_kicad/cooksense.kicad_sch   md5 7cd0d3540e2b33c924955d52f520d9a8
    source/cooksense.kicad_sch     md5 7cd0d3540e2b33c924955d52f520d9a8   IDENTICAL
    03_tscircuit/src/cooksense.tsx md5 33ca16f3683aa3dc3b3b232187451680
    source/cooksense.tsx           md5 33ca16f3683aa3dc3b3b232187451680   IDENTICAL

The archive is not a description of the board; it is the board's bytes.

## 4. Intent parity — the netlist graded against declared electrical intent

    E-INV  167/167 invariants hold against 06_build/netlists/cooksense.net   (raw exit 0)
    E-ADR   11/11 protection/topology ADRs cited by at least one invariant   (raw exit 0)

E-INV is the gate that is not self-consistency: DRC, ERC and parity all ask
whether the artifacts agree WITH EACH OTHER, and a design can be consistently
wrong across every one of them (that is exactly how the usb-hub-3s D1
reverse-polarity TVS defect passed five gates). E-INV compares the netlist
against assertions written from the ADRs, and E-ADR refuses to let a
protection ADR emit none.

## 5. BOM parity — per-refdes, against the SOURCE

    bom_source_check.py fab/bom.csv circuit.json --parts 02_parts   (raw exit 0)
      leg A: every BOM LCSC == the source's per-refdes code — PASS
      leg C: 28/28 R/C rows MPN-decoded-catalog-value == BOM label, over 61 BOM rows
      source: 208 coded refdes; vendored 44 part.yaml codes; ledger 151 vetted passive codes

`fab/bom.csv` and `fab/bom_jlc.csv` are byte-identical in this archive
(md5 `c491dd00e879e4a040b8828265832f2f` both), as are `fab/cpl.csv` and
`fab/cpl_jlc.csv` (md5 `38a332bd706310621671f5a624d02c76`). That is a
convenience today and NOT a licence to edit the reference copy — **`bom_jlc.csv`
and `cpl_jlc.csv` are the files JLC actually receives**, and ORDER_README §5-0
says so at the one point where a buyer might edit the wrong one.
