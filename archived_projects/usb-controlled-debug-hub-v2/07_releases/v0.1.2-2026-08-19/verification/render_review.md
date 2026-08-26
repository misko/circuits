# Exact-board render review — v0.1.2

subject: usb-controlled-debug-hub-v2
board_sha256: a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

Fresh top, bottom, northwest/southeast isometric and east/west edge views were
inspected. The twin mounts 168/168 CPL bodies. All four USB-A mouths and both
USB-C mouths face outward, their contacts sit on the intended lands, and the
machine connector mating-plane gate is 6/6 PASS.

This review specifically closes the v0.1.1 USB-C rendering defect. The
C165948 catalog body is recorded but rejected because its mating plane is
2.00 mm behind the exact HRO drawing/model datum. `J_DATA` and `J_POWER`
instead retain the exact manufacturer STEP with SHA-256
`f902880f83a1b397b76360ed8686b6132a66920b3c1aac8e98239315842ff43e`.
That selection is explicit and ref-scoped; it cannot silently apply to another
connector. The relocatable twin copies the selected file and records both
native and rejected-vendor identities.

Same-camera body measurement passes every resolvable subject: 34/34 top and
9/9 bottom. The other 125 top-side bodies are explicitly below the renderer's
2 mm/erosion resolution floor rather than missing; independent model coverage
is 168/168. The L_PD manufacturer-land adjudication, exposed-pad
multiplicity notices are documented without changing any CPL position or
rotation. `J_DATA` and `J_POWER` measure 0.148 mm and 0.122 mm from their
independently authored F.Fab expectations, respectively, with zero outward
excursion.

No visual placement/orientation defect is present in this corrected twin.
Final JLC rotation,
polarity, THT and assembly previews remain order-time human gates.
