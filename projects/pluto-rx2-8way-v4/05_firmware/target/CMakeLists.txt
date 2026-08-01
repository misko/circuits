cmake_minimum_required(VERSION 3.13)

set(MCU_BOARD "waveshare_rp2040_zero" CACHE STRING
    "Pico SDK board target; must match the fitted RP2040 module")
set(PICO_BOARD "${MCU_BOARD}" CACHE STRING "Pico SDK board" FORCE)

if(NOT DEFINED ENV{PICO_SDK_PATH})
    message(FATAL_ERROR "PICO_SDK_PATH is required for the target build")
endif()
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pluto_rx2_8way_v4 C CXX ASM)
pico_sdk_init()

add_executable(pluto_rx2_8way_v4
    main.c
    rx2_core.c
)
pico_generate_pio_header(pluto_rx2_8way_v4
    ${CMAKE_CURRENT_LIST_DIR}/switch_seq.pio)
target_include_directories(pluto_rx2_8way_v4 PRIVATE .)
target_link_libraries(pluto_rx2_8way_v4 PRIVATE
    pico_stdlib hardware_clocks hardware_dma hardware_pio)
pico_enable_stdio_usb(pluto_rx2_8way_v4 1)
pico_enable_stdio_uart(pluto_rx2_8way_v4 0)
pico_add_extra_outputs(pluto_rx2_8way_v4)
