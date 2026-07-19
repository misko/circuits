/* cook-hub pin map — THE board/firmware contract (spec §5 + D6/D7/D15).
 * Generated from the released schematic; if the board revs, this file revs
 * with it. All GPx are RP2350 (Pico 2) GPIO numbers.                     */
#ifndef COOK_HUB_PINMAP_H
#define COOK_HUB_PINMAP_H

/* I2C0: MLX90640 (0x33) + ambient SHT45 (0x44) — J3 */
#define PIN_I2C0_SDA 0
#define PIN_I2C0_SCL 1
/* I2C1: exhaust SHT45 (0x44) — J4 (separate bus: address clash, §3.4a) */
#define PIN_I2C1_SDA 2
#define PIN_I2C1_SCL 3

#define PIN_SPARE_GP4 4 /* J12 HOME / J13 EN / J14.5 (D7: enc XOR motor) */
#define PIN_WD_PULSE 5  /* HW watchdog retrigger, 5-20 Hz REQUIRED (D6)  */

#define PIN_HX_DAT 6 /* HX711 data  (J6 -> cook-loadcell) */
#define PIN_HX_CLK 7 /* HX711 clock                        */

#define PIN_DOOR 8   /* NC loop + EOL divider: 0=closed (D8)            */
#define PIN_ESTOP 9  /* monitors ESTOP_OK (post-Schmitt); 1=loop closed */
#define PIN_ARC 10   /* arc/flash reserve input (§4.3), TP32            */

#define PIN_SR_DATA 11  /* 74HC595 SER            */
#define PIN_SR_CLK 12   /* 74HC595 SRCLK          */
#define PIN_SR_LATCH 13 /* 74HC595 RCLK           */
#define PIN_RLY_EN 14   /* firmware enable: NAND->/OE AND coil-rail AND3.
                         * 10k pulldown: unprogrammed pin = disabled.    */
#define PIN_CONT_REQ 15 /* external contactor request -> LTV-817 -> J10 */

#define PIN_SPI0_MISO 16 /* MAX31856 SDO  */
#define PIN_SPI0_CS0 17  /* MAX31856 /CS  */
#define PIN_SPI0_SCK 18
#define PIN_SPI0_MOSI 19
#define PIN_SPI0_CS1 20 /* J15: future MAX31865 (D10) */

#define PIN_TT_A 21 /* turntable encoder A / STEP (D7, DNP headers) */
#define PIN_TT_B 22 /* turntable encoder B / DIR                    */

#define PIN_ADC_TH_PORT 26 /* ADC0: optical-port NTC (J9.1)      */
#define PIN_ADC_TH_ENCL 27 /* ADC1: enclosure NTC (J9.3)         */
#define PIN_ADC_SPARE 28   /* ADC2: spare NTC (J9.5) / door EOL via SJ1 */

/* Relay channel n (1..16) = 74HC595 chain bit: U3=QA..QH -> K1..K8,
 * U4=QA..QH -> K9..K16. Shift MSB-first: bit for K16 first.
 * Contact pair for channel n exits on J11 pins 2n-1 / 2n.               */
#define RELAY_CHANNELS 16

/* Hardware truth (ADR-0003) — firmware cannot override:
 *  - coils live only while WD_OK AND ESTOP_OK AND RLY_EN;
 *  - /OE released only while RLY_EN AND WD_OK;
 *  - WD_OK drops after 316-472 ms without PIN_WD_PULSE rising edges.    */
#endif
