#include "sl_iostream.h"
#include "sl_iostream_uart.h"
#include "sl_iostream_eusart.h"
#include "sl_common.h"
#include "dmadrv.h"
#include "sl_device_peripheral.h"
#include "sl_clock_manager.h"
#include "sl_hal_eusart.h"
#include "sl_hal_gpio.h"


#include "em_cmu.h"
 


#include "sl_cos.h"
 
// Include instance config 
 #include "sl_iostream_eusart_hehe_config.h"
 #include "sl_iostream_eusart_vcom_config.h"

// MACROs for generating name and IRQ handler function  
#if defined(EUART_COUNT) && (EUART_COUNT > 0) 
#define SL_IOSTREAM_EUSART_TX_IRQ_NUMBER(periph_nbr)     SL_CONCAT_PASTER_3(EUART, periph_nbr, _TX_IRQn)   
#define SL_IOSTREAM_EUSART_RX_IRQ_NUMBER(periph_nbr)     SL_CONCAT_PASTER_3(EUART, periph_nbr, _RX_IRQn)   
#define SL_IOSTREAM_EUSART_TX_IRQ_HANDLER(periph_nbr)    SL_CONCAT_PASTER_3(EUART, periph_nbr, _TX_IRQHandler)   
#define SL_IOSTREAM_EUSART_RX_IRQ_HANDLER(periph_nbr)    SL_CONCAT_PASTER_3(EUART, periph_nbr, _RX_IRQHandler)   
#define SL_IOSTREAM_EUSART_RX_DMA_SIGNAL(periph_nbr)     SL_CONCAT_PASTER_3(dmadrvPeripheralSignal_EUART, periph_nbr, _RXDATAV)
#define SL_IOSTREAM_EUSART_TX_DMA_SIGNAL(periph_nbr)     SL_CONCAT_PASTER_3(dmadrvPeripheralSignal_EUART, periph_nbr, _TXBL)
#define SL_IOSTREAM_EUSART_CLOCK_REF(periph_nbr)         SL_CONCAT_PASTER_2(SL_BUS_CLOCK_EUART, periph_nbr)  
#define SL_IOSTREAM_EUSART_PERIPHERAL(periph_nbr)        SL_CONCAT_PASTER_2(SL_PERIPHERAL_EUART, periph_nbr) 
#else
#define SL_IOSTREAM_EUSART_TX_IRQ_NUMBER(periph_nbr)     SL_CONCAT_PASTER_3(EUSART, periph_nbr, _TX_IRQn)   
#define SL_IOSTREAM_EUSART_RX_IRQ_NUMBER(periph_nbr)     SL_CONCAT_PASTER_3(EUSART, periph_nbr, _RX_IRQn)   
#define SL_IOSTREAM_EUSART_TX_IRQ_HANDLER(periph_nbr)    SL_CONCAT_PASTER_3(EUSART, periph_nbr, _TX_IRQHandler)   
#define SL_IOSTREAM_EUSART_RX_IRQ_HANDLER(periph_nbr)    SL_CONCAT_PASTER_3(EUSART, periph_nbr, _RX_IRQHandler)   
#define SL_IOSTREAM_EUSART_RX_DMA_SIGNAL(periph_nbr)     SL_CONCAT_PASTER_3(dmadrvPeripheralSignal_EUSART, periph_nbr, _RXDATAV)  
#define SL_IOSTREAM_EUSART_TX_DMA_SIGNAL(periph_nbr)     SL_CONCAT_PASTER_3(dmadrvPeripheralSignal_EUSART, periph_nbr, _TXBL)
#define SL_IOSTREAM_EUSART_CLOCK_REF(periph_nbr)         SL_CONCAT_PASTER_2(SL_BUS_CLOCK_EUSART, periph_nbr)  
#define SL_IOSTREAM_EUSART_PERIPHERAL(periph_nbr)        SL_CONCAT_PASTER_2(SL_PERIPHERAL_EUSART, periph_nbr) 
#endif


 
#define _SL_IOSTREAM_EUSART_HEHE_ENABLE_HIGH_FREQUENCY  SL_IOSTREAM_EUSART_HEHE_ENABLE_HIGH_FREQUENCY
 
#define _SL_IOSTREAM_EUSART_VCOM_ENABLE_HIGH_FREQUENCY  SL_IOSTREAM_EUSART_VCOM_ENABLE_HIGH_FREQUENCY

#if defined(EUART_COUNT) && (EUART_COUNT > 0)
#define SL_IOSTREAM_EUSART_CLOCK_SOURCE(periph_nbr)      SL_CONCAT_PASTER_2(cmuClock_EUART, periph_nbr)
#else
#define SL_IOSTREAM_EUSART_CLOCK_SOURCE(periph_nbr)      SL_CONCAT_PASTER_2(cmuClock_EUSART, periph_nbr)
#endif
 


// EM Events
#define SLEEP_EM_EVENT_MASK      (SL_POWER_MANAGER_EVENT_TRANSITION_ENTERING_EM0 \
                                  | SL_POWER_MANAGER_EVENT_TRANSITION_LEAVING_EM0)
static void events_handler(sl_power_manager_em_t from,
                           sl_power_manager_em_t to);
static sl_power_manager_em_transition_event_info_t events_info =
{
  .event_mask = SLEEP_EM_EVENT_MASK,
  .on_event = events_handler,
};
static sl_power_manager_em_transition_event_handle_t events_handle;
 


sl_status_t sl_iostream_eusart_init_hehe(void);

sl_status_t sl_iostream_eusart_init_vcom(void);


// Instance(s) handle and context variable 
static sl_iostream_uart_t sl_iostream_hehe;
sl_iostream_t *sl_iostream_hehe_handle = &sl_iostream_hehe.stream;

sl_iostream_uart_t *sl_iostream_uart_hehe_handle = &sl_iostream_hehe;
static sl_iostream_eusart_context_t  context_hehe;

static uint8_t  rx_buffer_hehe[SL_IOSTREAM_EUSART_HEHE_RX_BUFFER_SIZE];

static sli_iostream_uart_periph_t uart_periph_hehe = {
  .rx_irq_number = SL_IOSTREAM_EUSART_RX_IRQ_NUMBER(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO),
#if defined(SL_CATALOG_POWER_MANAGER_PRESENT)  
  .tx_irq_number = SL_IOSTREAM_EUSART_TX_IRQ_NUMBER(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO),
#endif
};

sl_iostream_instance_info_t sl_iostream_instance_hehe_info = {
  .handle = &sl_iostream_hehe.stream,
  .name = "hehe",
  .type = SL_IOSTREAM_TYPE_UART,
  .periph_id = SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO,
  .init = sl_iostream_eusart_init_hehe,
};
static sl_iostream_uart_t sl_iostream_vcom;
sl_iostream_t *sl_iostream_vcom_handle = &sl_iostream_vcom.stream;

sl_iostream_uart_t *sl_iostream_uart_vcom_handle = &sl_iostream_vcom;
static sl_iostream_eusart_context_t  context_vcom;

static uint8_t  rx_buffer_vcom[SL_IOSTREAM_EUSART_VCOM_RX_BUFFER_SIZE];

static sli_iostream_uart_periph_t uart_periph_vcom = {
  .rx_irq_number = SL_IOSTREAM_EUSART_RX_IRQ_NUMBER(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO),
#if defined(SL_CATALOG_POWER_MANAGER_PRESENT)  
  .tx_irq_number = SL_IOSTREAM_EUSART_TX_IRQ_NUMBER(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO),
#endif
};

sl_iostream_instance_info_t sl_iostream_instance_vcom_info = {
  .handle = &sl_iostream_vcom.stream,
  .name = "vcom",
  .type = SL_IOSTREAM_TYPE_UART,
  .periph_id = SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO,
  .init = sl_iostream_eusart_init_vcom,
};



sl_status_t sl_iostream_eusart_init_hehe(void)
{
  sl_status_t status;

  sl_iostream_eusart_config_t config_hehe = { 
    .eusart = SL_IOSTREAM_EUSART_PERIPHERAL(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO),
    .eusart_nbr = SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO,
    .bus_clock = SL_IOSTREAM_EUSART_CLOCK_REF(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO),
    .baudrate = SL_IOSTREAM_EUSART_HEHE_BAUDRATE,
    .parity = SL_IOSTREAM_EUSART_HEHE_PARITY,
    .flow_control = SL_IOSTREAM_EUSART_HEHE_FLOW_CONTROL_TYPE,
    .stop_bits = SL_IOSTREAM_EUSART_HEHE_STOP_BITS,
#if defined(EUSART_COUNT) && (EUSART_COUNT > 1)
    .port_index = SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO,
#endif
    .tx_port = SL_IOSTREAM_EUSART_HEHE_TX_PORT,
    .tx_pin = SL_IOSTREAM_EUSART_HEHE_TX_PIN,
    .rx_port = SL_IOSTREAM_EUSART_HEHE_RX_PORT,
    .rx_pin = SL_IOSTREAM_EUSART_HEHE_RX_PIN,
#if defined(SL_IOSTREAM_EUSART_HEHE_CTS_PORT)
    .cts_port = SL_IOSTREAM_EUSART_HEHE_CTS_PORT,
    .cts_pin = SL_IOSTREAM_EUSART_HEHE_CTS_PIN,
#endif
#if defined(SL_IOSTREAM_EUSART_HEHE_RTS_PORT)
    .rts_port = SL_IOSTREAM_EUSART_HEHE_RTS_PORT,
    .rts_pin = SL_IOSTREAM_EUSART_HEHE_RTS_PIN,
#endif
  };

  sl_iostream_dma_config_t rx_dma_config_hehe = {.src = (uint8_t *)&SL_IOSTREAM_EUSART_HEHE_PERIPHERAL->RXDATA,
                                                        .xfer_cfg = IOSTREAM_LDMA_TFER_CFG_PERIPH(SL_IOSTREAM_EUSART_RX_DMA_SIGNAL(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO))};

  sl_iostream_dma_config_t tx_dma_config_hehe = {.dst = (uint8_t *)&SL_IOSTREAM_EUSART_HEHE_PERIPHERAL->TXDATA,
                                                        .xfer_cfg = IOSTREAM_LDMA_TFER_CFG_PERIPH(SL_IOSTREAM_EUSART_TX_DMA_SIGNAL(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO))};

  sl_iostream_uart_config_t uart_config_hehe = {
    .rx_dma_cfg = rx_dma_config_hehe,
    .tx_dma_cfg = tx_dma_config_hehe,
    .rx_buffer = rx_buffer_hehe,
    .rx_buffer_length = SL_IOSTREAM_EUSART_HEHE_RX_BUFFER_SIZE,
    .enable_high_frequency = _SL_IOSTREAM_EUSART_HEHE_ENABLE_HIGH_FREQUENCY, 
    .lf_to_crlf = SL_IOSTREAM_EUSART_HEHE_CONVERT_BY_DEFAULT_LF_TO_CRLF,
    .rx_when_sleeping = SL_IOSTREAM_EUSART_HEHE_RESTRICT_ENERGY_MODE_TO_ALLOW_RECEPTION,
    .uart_periph = &uart_periph_hehe
  };
  uart_config_hehe.sw_flow_control = SL_IOSTREAM_EUSART_HEHE_FLOW_CONTROL_TYPE == SL_IOSTREAM_EUSART_UART_FLOW_CTRL_SOFT;
#if defined(SL_IOSTREAM_EUSART_HEHE_ASYNC_TX)
  uart_config_hehe.async_tx_enabled = SL_IOSTREAM_EUSART_HEHE_ASYNC_TX;
#else
  uart_config_hehe.async_tx_enabled = false;
#endif
  // Instantiate eusart instance 
  status = sl_iostream_eusart_init(&sl_iostream_hehe,
                                  &uart_config_hehe,
                                  &config_hehe,
                                  &context_hehe);
  EFM_ASSERT(status == SL_STATUS_OK);

  
  // Send VCOM config to WSTK
  uint8_t flow_control = COS_CONFIG_FLOWCONTROL_NONE;
  if (!uart_config_hehe.sw_flow_control) {
    switch (SL_IOSTREAM_EUSART_HEHE_FLOW_CONTROL_TYPE)
    {
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_NONE:
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_SOFT:
        flow_control = COS_CONFIG_FLOWCONTROL_NONE;
        break;
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_CTS:
        flow_control = COS_CONFIG_FLOWCONTROL_CTS;
        break;
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_RTS:
        flow_control = COS_CONFIG_FLOWCONTROL_RTS;
        break;
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_CTS_RTS:
        flow_control = COS_CONFIG_FLOWCONTROL_CTS_RTS;
        break;
      default:
        // Invalid flow control type
        EFM_ASSERT(0);
        break;
    }
  }
  sl_cos_config_vcom((uint32_t) SL_IOSTREAM_EUSART_HEHE_BAUDRATE, flow_control);
   

  return status;
}

sl_status_t sl_iostream_eusart_init_vcom(void)
{
  sl_status_t status;

  sl_iostream_eusart_config_t config_vcom = { 
    .eusart = SL_IOSTREAM_EUSART_PERIPHERAL(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO),
    .eusart_nbr = SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO,
    .bus_clock = SL_IOSTREAM_EUSART_CLOCK_REF(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO),
    .baudrate = SL_IOSTREAM_EUSART_VCOM_BAUDRATE,
    .parity = SL_IOSTREAM_EUSART_VCOM_PARITY,
    .flow_control = SL_IOSTREAM_EUSART_VCOM_FLOW_CONTROL_TYPE,
    .stop_bits = SL_IOSTREAM_EUSART_VCOM_STOP_BITS,
#if defined(EUSART_COUNT) && (EUSART_COUNT > 1)
    .port_index = SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO,
#endif
    .tx_port = SL_IOSTREAM_EUSART_VCOM_TX_PORT,
    .tx_pin = SL_IOSTREAM_EUSART_VCOM_TX_PIN,
    .rx_port = SL_IOSTREAM_EUSART_VCOM_RX_PORT,
    .rx_pin = SL_IOSTREAM_EUSART_VCOM_RX_PIN,
#if defined(SL_IOSTREAM_EUSART_VCOM_CTS_PORT)
    .cts_port = SL_IOSTREAM_EUSART_VCOM_CTS_PORT,
    .cts_pin = SL_IOSTREAM_EUSART_VCOM_CTS_PIN,
#endif
#if defined(SL_IOSTREAM_EUSART_VCOM_RTS_PORT)
    .rts_port = SL_IOSTREAM_EUSART_VCOM_RTS_PORT,
    .rts_pin = SL_IOSTREAM_EUSART_VCOM_RTS_PIN,
#endif
  };

  sl_iostream_dma_config_t rx_dma_config_vcom = {.src = (uint8_t *)&SL_IOSTREAM_EUSART_VCOM_PERIPHERAL->RXDATA,
                                                        .xfer_cfg = IOSTREAM_LDMA_TFER_CFG_PERIPH(SL_IOSTREAM_EUSART_RX_DMA_SIGNAL(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO))};

  sl_iostream_dma_config_t tx_dma_config_vcom = {.dst = (uint8_t *)&SL_IOSTREAM_EUSART_VCOM_PERIPHERAL->TXDATA,
                                                        .xfer_cfg = IOSTREAM_LDMA_TFER_CFG_PERIPH(SL_IOSTREAM_EUSART_TX_DMA_SIGNAL(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO))};

  sl_iostream_uart_config_t uart_config_vcom = {
    .rx_dma_cfg = rx_dma_config_vcom,
    .tx_dma_cfg = tx_dma_config_vcom,
    .rx_buffer = rx_buffer_vcom,
    .rx_buffer_length = SL_IOSTREAM_EUSART_VCOM_RX_BUFFER_SIZE,
    .enable_high_frequency = _SL_IOSTREAM_EUSART_VCOM_ENABLE_HIGH_FREQUENCY, 
    .lf_to_crlf = SL_IOSTREAM_EUSART_VCOM_CONVERT_BY_DEFAULT_LF_TO_CRLF,
    .rx_when_sleeping = SL_IOSTREAM_EUSART_VCOM_RESTRICT_ENERGY_MODE_TO_ALLOW_RECEPTION,
    .uart_periph = &uart_periph_vcom
  };
  uart_config_vcom.sw_flow_control = SL_IOSTREAM_EUSART_VCOM_FLOW_CONTROL_TYPE == SL_IOSTREAM_EUSART_UART_FLOW_CTRL_SOFT;
#if defined(SL_IOSTREAM_EUSART_VCOM_ASYNC_TX)
  uart_config_vcom.async_tx_enabled = SL_IOSTREAM_EUSART_VCOM_ASYNC_TX;
#else
  uart_config_vcom.async_tx_enabled = false;
#endif
  // Instantiate eusart instance 
  status = sl_iostream_eusart_init(&sl_iostream_vcom,
                                  &uart_config_vcom,
                                  &config_vcom,
                                  &context_vcom);
  EFM_ASSERT(status == SL_STATUS_OK);

  
  // Send VCOM config to WSTK
  uint8_t flow_control = COS_CONFIG_FLOWCONTROL_NONE;
  if (!uart_config_vcom.sw_flow_control) {
    switch (SL_IOSTREAM_EUSART_VCOM_FLOW_CONTROL_TYPE)
    {
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_NONE:
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_SOFT:
        flow_control = COS_CONFIG_FLOWCONTROL_NONE;
        break;
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_CTS:
        flow_control = COS_CONFIG_FLOWCONTROL_CTS;
        break;
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_RTS:
        flow_control = COS_CONFIG_FLOWCONTROL_RTS;
        break;
      case SL_IOSTREAM_EUSART_UART_FLOW_CTRL_CTS_RTS:
        flow_control = COS_CONFIG_FLOWCONTROL_CTS_RTS;
        break;
      default:
        // Invalid flow control type
        EFM_ASSERT(0);
        break;
    }
  }
  sl_cos_config_vcom((uint32_t) SL_IOSTREAM_EUSART_VCOM_BAUDRATE, flow_control);
   

  return status;
}



void sl_iostream_eusart_init_instances(void)
{
  
  // Enable power manager notifications
  sl_power_manager_subscribe_em_transition_event(&events_handle, &events_info);
   
  // Instantiate eusart instance(s) 
  
  sl_iostream_eusart_init_hehe();
  
  sl_iostream_eusart_init_vcom();
  
}


void SL_IOSTREAM_EUSART_TX_IRQ_HANDLER(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO)(void)
{
  sl_iostream_eusart_irq_handler(&sl_iostream_hehe);
}

void SL_IOSTREAM_EUSART_RX_IRQ_HANDLER(SL_IOSTREAM_EUSART_HEHE_PERIPHERAL_NO)(void)
{
  sl_iostream_eusart_irq_handler(&sl_iostream_hehe);
}
void SL_IOSTREAM_EUSART_TX_IRQ_HANDLER(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO)(void)
{
  sl_iostream_eusart_irq_handler(&sl_iostream_vcom);
}

void SL_IOSTREAM_EUSART_RX_IRQ_HANDLER(SL_IOSTREAM_EUSART_VCOM_PERIPHERAL_NO)(void)
{
  sl_iostream_eusart_irq_handler(&sl_iostream_vcom);
}



 
sl_power_manager_on_isr_exit_t sl_iostream_eusart_hehe_sleep_on_isr_exit(void)
{
  return sl_iostream_uart_sleep_on_isr_exit(&sl_iostream_hehe);
}
 
sl_power_manager_on_isr_exit_t sl_iostream_eusart_vcom_sleep_on_isr_exit(void)
{
  return sl_iostream_uart_sleep_on_isr_exit(&sl_iostream_vcom);
}

 
static void events_handler(sl_power_manager_em_t from,
                           sl_power_manager_em_t to)
{
  (void) from;
  if (to == SL_POWER_MANAGER_EM0) {
    
    if (sl_iostream_uart_hehe_handle->stream.context != NULL) {
      sl_iostream_uart_wakeup(sl_iostream_uart_hehe_handle);
    }
    
    if (sl_iostream_uart_vcom_handle->stream.context != NULL) {
      sl_iostream_uart_wakeup(sl_iostream_uart_vcom_handle);
    }
    
  } else if (to < SL_POWER_MANAGER_EM2){
    // Only prepare for sleep to EM2 or less
    
    if (sl_iostream_uart_hehe_handle->stream.context != NULL) {
      sl_iostream_uart_prepare_for_sleep(sl_iostream_uart_hehe_handle);
    }
    
    if (sl_iostream_uart_vcom_handle->stream.context != NULL) {
      sl_iostream_uart_prepare_for_sleep(sl_iostream_uart_vcom_handle);
    }
    
  }
}

