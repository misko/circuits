/* Hardware-watchdog service stub — spec §6.5 contract.
 * The SN74LVC1G123 monostable (U7) is retriggered by RISING EDGES on
 * PIN_WD_PULSE. Timeout band 316-472ms (390k/1u, ADR-0003). Firmware
 * must toggle at 5-20 Hz FROM THE SENSOR/SUPERVISOR LOOP — never from an
 * ISR or a dedicated task that could survive a hung main loop (that would
 * recreate the firmware-only watchdog §6.5 forbids).                    */
#ifndef COOK_HUB_WATCHDOG_H
#define COOK_HUB_WATCHDOG_H
#include <stdbool.h>

void wd_init(void);       /* pin low; monostable stays untriggered at boot */
/* Call ONCE per healthy main-loop iteration; internally rate-limits to
 * ~10 Hz edges. A wedged loop stops calls -> WD_OK drops -> hardware
 * kills /OE and the coil rail regardless of firmware state. */
void wd_service(void);
/* Deliberately starve the watchdog (test hook for §16.2 bench test). */
void wd_test_starve(bool on);
#endif
