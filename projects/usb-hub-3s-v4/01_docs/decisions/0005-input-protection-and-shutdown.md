---
id: 0005
date: 2026-08-10
status: accepted
---
# 0005 — Passive input protection and enable-gated shutdown

## Context

D1 removes active sustained-overvoltage cutoff, but the board still needs a
coordinated input path for overload, reverse polarity and ordinary hot-plug
transients. A 3S pack and low-ESR module ceramics connected through leads can
ring; the whole board also needs a low-current stored state.

## Decision

Use Phoenix 1715022 two-position terminal -> user-installed 10A MINI fuse in
Keystone 3568 -> DMP3013SFV-7 series P-FET with BZT52C12-7-F 12V gate-source
clamp -> protected VIN with SMBJ15A and Rubycon 35TZV100M6.3X8 100uF/35V
electrolytic damping. The user cable is an XT60-to-bare-wire pigtail and the
terminal polarity is marked on both PCB faces. EG1218 SW1 grounds the common
converter EN bus in OFF.

## Consequences

The fuse protects the input trunk; independent port devices regulate output
fault current. The TVS is placed after the reverse-polarity FET so it does not
forward-conduct into a reversed pack. SMBJ15A is only a transient clamp and the
first article must capture the real lead/hot-plug waveform. No protection from
sustained source overvoltage or converter fail-high is claimed. Stage 2 must
prove the complete maximum-temperature OFF current against the <=1mA limit.
The screw terminal is not keyed, so the FET is a protection layer rather than a
reason to omit large, unambiguous polarity marking.
