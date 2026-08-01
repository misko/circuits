review_kind: RF_PCB
subject: pluto-rx2-8way-v4 04_kicad/pluto_rx2_8way_v4.kicad_pcb
reviewer: redteam-agent (GPT-5 RF PCB lens)
independence: independent-from-design-author
source_commit: bc1fb1003cd9b7f06c70b15d973c5c018d0ff458
artifact_sha256: 72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7
design_verdict: SOUND

# Independent RF PCB review

requirement: RF-PCB-STACKUP PASS
requirement: RF-PCB-LAUNCH PASS
requirement: RF-PCB-RETURN PASS
requirement: RF-PCB-LENGTH PASS
requirement: RF-PCB-FENCE PASS
requirement: RF-PCB-COUPLING PASS
requirement: RF-PCB-PADSEP PASS

The exact board carries the authored JLC04121H-7628 1.2 mm four-layer stack,
35 um outer / 15.2 um inner copper, 0.2104 mm top-to-In1 dielectric, 0.360 mm
masked CPWG trace and 0.2005 mm coplanar gap. The independent field evidence
converges to 52.0877 ohm, within the declared 50 ohm +/-10% band.

All SMA launches retain direct, via-free F.Cu RF arms. In1.Cu is the continuous
GND reference and contains no signal track; the only reviewed crossing of the
ANT4 path is moved to In2.Cu, leaving In1 uninterrupted. The realized fence
gate grades 22/22 configured arm sides with 1.1769 mm worst interior aperture
against the 1.1910 mm maximum. The eight routed arms span only 0.1657 mm,
inside the 1.0 mm relative-copper limit.

No unplanned RF branch, stub, neckdown, layer transition, return-slot crossing,
or coupling wall was found. The repaired module-control resistors clear every
foreign land by 0.220 mm and the paste apertures do not intrude; the SW_V4
escape retains its reviewed In2 crossing. DRC, explicit geometry, RF length,
fence and pad-separation gates agree on the exact artifact.

TDR/VNA data remains mandatory first-article evidence for assembled launch,
loss, isolation and phase behavior. It does not substitute for or negate this
exact PCB geometry verdict.
