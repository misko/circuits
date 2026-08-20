# commission journal

## 2026-08-20 — start

- state: working
- subject: new clean project `usb-controlled-debug-hub-2a-v1`
- input: user requested a board similar to the two-USB-C debug hub with each
  USB-A capable of 2 A, and asked to preserve high-cost purchased parts where
  possible.
- measured: predecessor contract is 2.58 A total, one TPS56637 is rated 6 A,
  and its 15 V/3 A PD source provides 45 W. New external output alone is 40 W.
- finding: the predecessor KH-AF90DIP-112 authority publishes no current
  rating; GCT USB1130-15-A publishes 3 A/contact.
- decision: evaluate 20 V/3 A PD with two retained 6 A converters and two
  two-port banks. Firmware remains forbidden.
- next: close exact input protection and current-limit corners; build a
  preliminary quantity-five BOM and run the early manufacturing gate.

## 2026-08-20 — early boundary closed

- `early_design_check.py`: PASS 3/3 (`D-SPEC/E-PATH`, `E-SURGE`, adopted
  commission contracts).
- The gate rejected TPS259827O before schematic generation because the
  TVS2200 28.35 V worst clamp exceeds its 24 V recommended operating maximum.
- TPS26630 passed electrically but exact TI public stock was zero. It was not
  replaced by the similarly named clone because that is a different device.
- Selected candidate TPS16630PWPR is 60 V operating/67 V absolute, provides
  programmable UVLO/OVP and showed over 1,250 exact TI units publicly stocked.
- Machine corners: UVLO rising 16.1171–17.9106 V; OVP rising
  22.3402–24.7388 V. The former rejects 15 V PDOs and accepts 20 V PDOs; the
  latter stays below the retained converters' 28 V operating ceiling.
- Initial 5 V service proof closes at 4.785 V at the mated 2 A test plug with a
  90 mOhm path allocation. This is a strict placement/routing/first-article
  budget, not permission to round copper resistance down.
- next: close aggregate/port breaker fault timing and inrush, then issue the
  complete preliminary quantity-five BOM for JLC prelayout screening.
