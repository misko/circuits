# Pluto RX2 eight-way v5 enclosure v0.1.2

Status: **CAD_READY**

Based on PCB release: **v0.2.1-2026-08-14**

This immutable release promotes the physically selected `4.25 mm` modeled
pilot from the v0.1.1 insert coupon into all four production base pockets.
The exact insert remains the E-Z LOK E-Z Press flanged M3-0.5
`260-M3-BR`/`260-M3-CR`, with its truthful `4.216 mm` nominal body recorded.

Because an FDM modeled hole may print undersize, the enclosure contract marks
the pilot basis as `coupon_qualified`; it does not pretend the nominal CAD
dimensions have interference. The coupon ladder remains `4.15`, `4.25`,
`4.35`, and `4.45 mm` for process requalification.

## Printable files

- `meshes/base.stl` — production insert pockets are 4.25 mm in the model
- `meshes/lid.stl`
- `meshes/insert_coupon.stl`

The assembled enclosure measures approximately `96.8 x 71.8 x 27.1 mm`.
The insert coupon is `54 x 20 x 6 mm`.

## Verification

- exact subject bindings: 5/5 PASS;
- connector/interface coverage: 62/62 PASS;
- fastener geometry: 9/9 PASS;
- printable meshes: 3/3 PASS;
- exact STEP-component/case intersection: EMPTY, 0 mm^3;
- thermal-plan consistency: 2/2 PASS;
- physical evidence: INCOMPLETE, 0/3.

The self-contained replay package is in `package/`. It contains the exact PCB,
STEP, interface, authored SCAD, printable meshes, collision evidence, and a
path-rebased `replay/enclosure.yaml` configuration.

## Remaining physical validation

1. Print the regenerated base and lid using the qualified process.
2. Install all four inserts and check seating, boss condition, spin-out, and
   pull-out tendency.
3. Install the actual assembled PCB and confirm lid closure without force.
4. Mate all intended SMA, USB-C, SWD, and bench-power interfaces together.
5. Record that evidence and mint a new immutable enclosure release.

This release remains `CAD_READY`; it is not `PRINT_VERIFIED` or
`THERMALLY_VERIFIED`, and it does not change the PCB release's order state.
