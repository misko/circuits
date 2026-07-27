# photos/ — MISSING, and the exact files needed

**I could not add the photographs.** They were pasted into a chat session, not
written to disk, and nothing matching was on the filesystem. This directory is
the named home for them; drop the files in and they slot into the references
already written in the parent `README.md`.

## Expected filenames

| filename | what it shows | why it matters |
|---|---|---|
| `board-A-genuine-top.jpg` | Board A top side | The **RF shield can** over the AD9363, `Pluto+` logo, cartoon, 一蓑烟雨任平生, SMA silk `T2 R2 R1 T1`, single `CLK-IN` U.FL, `DFU` button, `5V_IN` + `USB` micro-B, HanRun RJ45 |
| `board-A-genuine-bottom.jpg` | Board A bottom side | Four corner mounting holes with plated pads, SD slot, headers |
| `board-B-clone-top.jpg` | Board B top side | **No shield can — AD9363 bare and readable**, `CLK_IN` *and* `CLK_OUT` U.FL, `BOOT MODE` switch table, `DAC1/DAC2` + `GPO0`–`GPO3` pads, SMA silk `TX2A RX2A RX1A TX1A` |
| `board-B-clone-bottom.jpg` | Board B bottom side | `S1` boot switch, `MIO` test points, `AD9361_CLKOUT` silk, different logo |

Any format is fine; the names are what the parent doc points at.

## Why these specific views are worth keeping

The top-side photos are the **field identification evidence** — the shield can
and the second U.FL are what separate a genuine Pluto+ from the 2025 clone in
one glance, and that distinction is load-bearing here because the two boards
measure 0.32 mm apart across the SMA span.

The bottom-side photos show the four corner mounting holes, which are the only
published-adjacent route to taking mechanical load off the SMA connectors.
Their positions are **not** on the vendor's assembly layer, so a photo is
currently the only record that they exist at all.
