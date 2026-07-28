# 05_firmware/Makefile — host test harness for the pure logic.
#
# The MCU is a VARIABLE, never a constant (05_firmware/contracts.md): a part
# swap is a sourcing decision, not a rewrite. This board's MCU is the one in
# the BOM, 02_parts/XU316-1024-TQ128-I24/.
MCU ?= xu316-1024-tq128-i24

CC     ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -O2

.PHONY: test clean
## test — run every host-runnable logic test. Requires no toolchain for $(MCU).
test:
	@echo "MCU = $(MCU)  (host test only; no target code is built here)"
	$(CC) $(CFLAGS) -DCAL_BURST_SELFTEST -D_GNU_SOURCE cal_burst.c -o /tmp/cal_burst_selftest -lm
	@/tmp/cal_burst_selftest

clean:
	@rm -f /tmp/cal_burst_selftest
