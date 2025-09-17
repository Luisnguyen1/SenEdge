#include "sl_event_handler.h"

#include "sl_board_init.h"
#include "sl_clock_manager.h"
#include "sl_hfxo_manager.h"
#include "sl_board_control.h"
#include "sl_tflite_micro_init.h"
#include "sl_debug_swo.h"
#include "sl_mvp.h"
#include "sl_gpio.h"
#include "sl_i2cspm_instances.h"
#include "sl_iostream_init_eusart_instances.h"
#include "sl_simple_led_instances.h"
#include "sl_spidrv_instances.h"
#include "sl_iostream_init_instances.h"
#include "sl_cos.h"
#include "sl_iostream_handles.h"

void sli_driver_permanent_allocation(void)
{
}

void sli_service_permanent_allocation(void)
{
}

void sli_stack_permanent_allocation(void)
{
}

void sli_internal_permanent_allocation(void)
{
}

void sl_platform_init(void)
{
  sl_board_preinit();
  sl_clock_manager_runtime_init();
  sl_hfxo_manager_init_hardware();
  sl_board_init();
}

void sli_internal_init_early(void)
{
}

void sl_driver_init(void)
{
  sl_debug_swo_init();
  sli_mvp_init();
  sl_gpio_init();
  sl_i2cspm_init_instances();
  sl_simple_led_init_instances();
  sl_spidrv_init_instances();
  sl_cos_send_config();
}

void sl_service_init(void)
{
  sl_board_configure_vcom();
  sl_hfxo_manager_init();
  sl_iostream_init_instances_stage_1();
  sl_iostream_init_instances_stage_2();
}

void sl_stack_init(void)
{
}

void sl_internal_app_init(void)
{
  sl_tflite_micro_init();
}

void sli_platform_process_action(void)
{
}

void sli_service_process_action(void)
{
}

void sli_stack_process_action(void)
{
}

void sli_internal_app_process_action(void)
{
}

void sl_iostream_init_instances_stage_1(void)
{
  sl_iostream_eusart_init_instances();
}

void sl_iostream_init_instances_stage_2(void)
{
  sl_iostream_set_console_instance();
}

