subject: pluto-rx2-8way-v4 48688aa3 connectors
date: 2026-07-31
reviewer: pin-review
context-given: zero-context
design_verdict: SOUND
order_verdict: ORDER

KH-SMA-KE-Z connector group — J_ANT1..J_ANT8, J_RX1, J_RX2

VERDICT: PASS

Evidence: vendor PDF sheet 2/2 shows `5-Ø1.4`: one centre hole plus four corner holes on a 5.08 × 5.08 mm square. The flange view identifies `4-SQ0.9` corner posts, while the coaxial centre conductor is distinct. The part is a vertical standard SMA jack/receptacle: external 1/4-36UNEF shell and female centre contact, not RP-SMA. PDF SHA-256 matches `part.yaml`: `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`.

The vendor drawing assigns no numbers to the four mechanically identical shell posts. Therefore pin-1 corner and package winding are not applicable: pin 1 is central, and pins 2–5 are interchangeable shell/GND posts. The dossier’s 2→3→4→5 corner sequence is CCW in its stated top-view frame, but mirroring that sequence cannot change electrical connectivity.

J_ANT1 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT1.  
J_ANT1 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT2 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT2.  
J_ANT2 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT3 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT3.  
J_ANT3 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT4 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT4.  
J_ANT4 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT5 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT5.  
J_ANT5 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT6 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT6.  
J_ANT6 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT7 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on ANT7.  
J_ANT7 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_ANT8 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on RX1_MAIN.  
J_ANT8 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_RX1 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on RX1_MAIN.  
J_RX1 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

J_RX2 pin 1 (RF): expected centre conductor on an RF signal net vs dossier shows centre pad on RX2_OUT.  
J_RX2 pins 2–5 (GND): expected four corner shell posts on ground vs dossier shows all four on GND.

Symmetry: all ten instances have exactly five THT pads at identical local coordinates; pin 1 is always centre/RF, pins 2–5 are always corner/GND, and every centre net is signal-like. No structural divergence, centre/shell swap, missing pad, gender mismatch, or electrically meaningful mirror was found.
