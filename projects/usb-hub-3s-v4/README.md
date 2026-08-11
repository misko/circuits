# USB Hub 3S v4

Fresh, power-only successor to `usb-hub-3s-v3`. Despite the short name, this
is not a USB data hub: it distributes regulated 5 V from a 3S LiPo pack to
three charge-only USB-A ports and one Raspberry Pi 4 USB-C power input.

Status: **commission complete; design not yet generated and not orderable**.
There is no current release.

The live requirements and assumptions are in `01_docs/BRIEF.md`. Machine-read
power contracts are in `03_src/rules/requirements.yaml` and
`03_src/rules/power_tree.yaml`. `01_docs/STATUS.md` identifies the current
pipeline stage.

The full build entry point is `bash 03_src/rebuild_all.sh`, but it is expected
to fail closed until the parts and schematic stages supply their required
inputs. Do not treat a commission-stage scaffold as a PCB design.
