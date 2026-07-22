# Changelog — crow-array-pod

## v1.1 — 2026-07-19

RJ45 termination (A4 user request, D11/ADR-0004): J1 becomes an Amphenol
RJHSE-5384 jack — the same part as every crow-array-central port — cable
through the M12 gland, solid-core RJ45 plug field-crimped inside. Net map
is contact-for-contact the v1.0 terminal map = the central v1.0 sealed
port map (central D28); LED tails NC; shield tails on the SHIELD net
(D7 DNP bond preserved). Jack + exposed-plug volume placed inside the
1551WY lid's 81x31 full-height recess, opening WEST toward the gland
(clearance math in ADR-0004 — CONDITIONAL FIT, nominal +0.24mm, top EMI
tabs compress on the lid, FIRST-ARTICLE lid-close gate; also documents
v1.0's latent terminal-vs-lid interference). Mic/beeper acoustic layout
untouched; full KRT re-route with a reserved GND escape corridor for the
jack's tail field. Gates: ERC 0, audit PASS (new I2 recess containment),
DRC 0/0/0 severity-all with parity, netlist delta J1-only, twin exit 0,
stock 15/15, fresh-context J1 interop pin review, policy audit zero FAIL.
Released: v1.1-2026-07-19

## v1.0 — 2026-07-18
First orderable release. AOM-5024L + OPA1678 balanced pod per the Rev-A
working design §3/3A/4: 3.9k mic bias from RC-filtered 5V, x1.5 + unity
inverter (diff x3), 68R/leg isolation, TPD2E2U06 at entry (D5), SS14
flyback + empty TVS position (ADR-0002), CM-choke/shield reserves
unpopulated (D7), 8-pos screw terminal = T568B pin-for-pin (D6),
1551WY max-PCB outline + boss holes (D4). Gates: ERC 0, audit PASS,
DRC 0/0/0 severity-all with parity, twin exit 0 (evidence-backed
adjudications), stock 15/15 coded lines verified, policy audit zero FAIL.
Released: v1.0-2026-07-18
