# USB hub v1.12 enclosure candidate

This is a support-free FDM **draft**, derived without changing the immutable
v1.12 PCB release. It uses a floor-down base, roof-down lid, and four flat
edge panels. Four M3 inserts mount the board; four separate M3 inserts close
the lid so connector loads and lid torque do not bend the PCB.

Do not call this case CAD-ready yet. The sealed v1.12 STEP omits J1-J5, F2,
Q1-Q6, U3-U5, and has no SW1 model. The fitted blade fuse is also absent.
The skill's STEP inspection records that failure. The larger, provisional
openings in `enclosure.yaml` come from the exact PCB anchors and F.Fab bodies,
not from pretending the incomplete STEP is authoritative.

From the repository root:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/extract_board_interface.py \
  projects/usb-hub-3s-v3/07_releases/v1.12-2026-07-28/source/usb_hub_3s_v2.kicad_pcb \
  -o projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12/board-interface.json \
  --access-ref J1 --access-ref J2 --access-ref J3 --access-ref J4 \
  --access-ref J5 --access-ref F1 --access-ref SW1

/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  projects/usb-hub-3s-v3/03_src/mechanical/enclosure.yaml \
  --root projects/usb-hub-3s-v3 \
  --build-dir projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12

/usr/bin/python3 skills/pcb-enclosure/scripts/inspect_step.py \
  projects/usb-hub-3s-v3/07_releases/v1.12-2026-07-28/3d/usb_hub_3s_v2.step \
  --interface projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12/board-interface.json \
  --output projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12/step-inspection.json

/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure.py \
  projects/usb-hub-3s-v3/03_src/mechanical/enclosure.yaml \
  --root projects/usb-hub-3s-v3 \
  --build-dir projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12 \
  --step-inspection projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12/step-inspection.json \
  --report projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12/verification.json
```

Expected inspection and verification result: exit 1/`FAIL`, naming the missing
solids. A supplemental
assembly model must be created outside the sealed release, then hash-bound and
collision-checked before the enclosure can reach `CAD_READY`.

Before any fit status, measure the received SW1 actuator, the installed MINI
fuse height, and the actual USB-C cable overmold. Print the insert coupon first.
Closed-case thermal validation must repeat the declared 6 A USB-A + 3 A USB-C
load case while logging the fuse clips and both buck-converter hot zones.
