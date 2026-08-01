MCU_BOARD ?= waveshare_rp2040_zero
BUILD_DIR ?= build
CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror

.PHONY: test firmware

test:
	$(CC) $(CFLAGS) -Itarget target/rx2_core.c target/test_rx2_core.c -o /tmp/pluto_rx2_v4_core_test
	/tmp/pluto_rx2_v4_core_test
	python3 -m unittest -v test_rx2ctl.py

firmware:
	cmake -S target -B $(BUILD_DIR) -DMCU_BOARD=$(MCU_BOARD)
	cmake --build $(BUILD_DIR)
