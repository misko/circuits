# fixtures/twin_overlay — JLC CAD for the two refs the A-RENDER gate is pinned on

`easyeda/<LCSC>/` is the same layout `jlc_twin.py` writes under its outdir, so
`twin_overlay.py --twin-dir` points straight at it.

Every file here was fetched by `easyeda2kicad` into
`projects/crow-recorder-central-v2/06_build/twin_v15/easyeda/` on 2026-07-25 —
**the same run that produced the SEALED v1.5 twin renders the tests grade.**

| LCSC | part | why it is here |
|---|---|---|
| `C3020560` | GCT USB4105 USB-C, board ref J2 | the DEFECT: mounted at a fit it had just rejected, rendered 90 deg out |
| `C381116` | DC barrel jack, board ref J1 | the CONTROL: 5.686 mm off its courtyard and the render is FAITHFUL |
| `C377773` | 0805 MLCC, ref C_vb | J2's neighbours. Present so J2 is GRADEABLE at all: a |
| `C25905` | 0402 R, refs R_cc1/R_cc2 | part with no expected body cannot be masked out of |
| `C25767` | 0402 R, ref R_vb1 | J2's measurement window, so the gate declares J2 |
| `C25792` | 0402 R, ref R_vbld | UNRESOLVABLE — correctly, but uselessly for the test |

Those four neighbours are the complete set within `CLEAR_MM` (0.5 mm) of J2's
expected body: `C_vb` 0.00, `R_vb1` 0.00, `R_cc2` 0.00, `R_cc1` 0.00,
`R_vbld` 0.293 mm. With them present the fixture reproduces the full-cache
numbers EXACTLY — J2 centre delta 1.435 mm / outward 1.491 mm, J1 0.046 /
0.000 — on a 644 KB fixture instead of a 47-part, 100 MB cache.

Only `jlc.pretty/*.kicad_mod` and `jlc.3dshapes/*.wrl` are vendored — the
`.step` siblings are 4 MB and nothing reads them.

**One byte-level edit, deliberate:** the absolute `(model "...")` path
easyeda2kicad bakes in at fetch time is rewritten to
`/nonexistent-by-design/jlc.3dshapes/<same name>`. The real path pointed into
an untracked `06_build/` tree, so on any other machine the fixture would have
resolved differently depending on what happened to be on disk. Pointing it at
a path that can never exist makes the fixture hermetic AND makes every test
exercise `twin_overlay.resolve_mesh()`'s beside-the-footprint fallback, which
is the path a moved cache actually takes.

Everything else is unmodified. The numbers these files must reproduce (they
are asserted in `tests/t1_twin_overlay.py`):

- `C381116` mesh plan bbox `-8.300 -5.000 1.000 9.400` mm in the model frame,
  centre `(-3.6500, +2.2000)`; its footprint mounts the model at `rot_z 90`.
- `C3020560` mesh plan bbox `-4.4699 -4.9225 4.4699 2.6325` mm, centre
  `(0.0000, -1.1450)`; `rot_z 0`.
