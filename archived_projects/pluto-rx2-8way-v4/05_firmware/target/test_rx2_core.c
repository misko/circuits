#include "rx2_core.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
    const uint8_t expected_codes[RX2_STATE_COUNT] =
        {0u, 4u, 2u, 6u, 1u, 5u, 3u, 7u};
    struct rx2_config config = rx2_config_default();
    struct rx2_status status;

    assert(rx2_config_valid(&config));
    assert(rx2_frame_samples(&config) == 62464u);
    for (uint8_t state = 0; state < RX2_STATE_COUNT; ++state) {
        uint32_t dwell = state == 7u ? 4224u : 8320u;
        assert(rx2_gpio_code(state) == expected_codes[state]);
        assert(rx2_dwell_samples(&config, state) == dwell);
        assert((rx2_schedule_word(&config, state) & 0x0fu) ==
               expected_codes[state]);
        assert((rx2_schedule_word(&config, state) >> 4) ==
               dwell - RX2_PIO_OVERHEAD_SAMPLES);
    }
    assert(rx2_gpio_code(8u) == RX2_ALL_OFF_GPIO_CODE);

    rx2_status_init(&status);
    assert(!status.running && !status.muted && status.selected_state == 0u);
    assert(rx2_select(&status, 7u));
    assert(status.selected_state == 7u && !status.running);
    assert(!rx2_select(&status, 8u));
    rx2_mute(&status);
    assert(status.muted && !status.running);
    rx2_start(&status);
    assert(status.running && !status.muted && status.selected_state == 0u);
    for (unsigned i = 0; i < RX2_STATE_COUNT; ++i)
        rx2_note_transition(&status);
    assert(status.frame_count == 1u && status.transition_count == 8u &&
           status.selected_state == 0u);

    config.blank_samples = 0u;
    config.ordinary_clean_samples = 1u;
    config.reference_clean_samples = 1u;
    assert(!rx2_config_valid(&config));
    assert(!rx2_set_config(&status, &config));

    puts("rx2_core: OK");
    return 0;
}
