# ADR-0001 — System decomposition + Phase-1 scope (ribbon interception first)

status: accepted
date: 2026-07-22
tags: topology

## Decision
Phase 1 = the ribbon-interception core: (1) Board C passive interposer
(coupon-gated, ADR-0005) and (2) ONE CookSense board merging the brief's
Boards A+B (sensing + hardware safety + the 12-relay matrix selector),
IF keypad-line length allows co-location near the OEM controller — the
keepout/mechanical analysis decides the split, exactly as it decides
HAT-vs-sidecar. cook-loadcell v1.0 reused as-is (Board D). Sensor
adapters (E) skipped for first prototype (wire Adafruit modules direct).
Boards F/G deferred to Phase 2 per the brief.

## Why separate boards at all
(1) boards live where their connectors/sensors physically are; (2) the
keypad domain touching the OEM must be galvanically isolated from SELV
logic (>=6mm, milled slots, no shared common); (3) the unproven parts
(CN1 tongue) are isolated so a revision never respins the rest — the
brief's contingency matrix depends on this (C1/C3 hold A/B fixed).

## D4_UNKNOWN policy (spec-tension T3)
Passed through + test point + selector fitted but locked out until its
electrical function is established (Gate 3). Never selected by default.
