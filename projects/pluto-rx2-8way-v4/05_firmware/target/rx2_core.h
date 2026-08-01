#ifndef RX2_CORE_H
#define RX2_CORE_H

#include <stdbool.h>
#include <stdint.h>

#define RX2_STATE_COUNT 8u
#define RX2_PIO_OVERHEAD_SAMPLES 4u
#define RX2_ALL_OFF_GPIO_CODE 0x08u

struct rx2_config {
    uint32_t sample_rate_hz;
    uint32_t ordinary_clean_samples;
    uint32_t reference_clean_samples;
    uint32_t blank_samples;
};

struct rx2_status {
    struct rx2_config config;
    uint32_t frame_count;
    uint32_t transition_count;
    uint8_t selected_state;
    bool running;
    bool muted;
};

struct rx2_config rx2_config_default(void);
bool rx2_config_valid(const struct rx2_config *config);
uint32_t rx2_frame_samples(const struct rx2_config *config);
uint8_t rx2_gpio_code(uint8_t state);
uint32_t rx2_dwell_samples(const struct rx2_config *config, uint8_t state);
uint32_t rx2_schedule_word(const struct rx2_config *config, uint8_t state);
void rx2_status_init(struct rx2_status *status);
bool rx2_select(struct rx2_status *status, uint8_t state);
void rx2_mute(struct rx2_status *status);
void rx2_start(struct rx2_status *status);
void rx2_stop(struct rx2_status *status);
bool rx2_set_config(struct rx2_status *status,
                    const struct rx2_config *config);
void rx2_note_transition(struct rx2_status *status);

#endif
