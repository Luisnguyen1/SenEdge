/***************************************************************************//**
 * @file
 * @brief Top level application functions
 *******************************************************************************
 * # License
 * <b>Copyright 2022 Silicon Laboratories Inc. www.silabs.com</b>
 *******************************************************************************
 *
 * The licensor of this software is Silicon Laboratories Inc. Your use of this
 * software is governed by the terms of Silicon Labs Master Software License
 * Agreement (MSLA) available at
 * www.silabs.com/about-us/legal/master-software-license-agreement. This
 * software is distributed to you in Source Code format and is governed by the
 * sections of the MSLA applicable to Source Code.
 *
 ******************************************************************************/
#include "app.h"

#include "app_assert.h"
#include "app_log.h"
#include "sl_bt_api.h"
#include "gatt_db.h"

#include "audio_classifier.h"     // để gọi audio_classifier_init()
#include <string.h>
#include <stdio.h>

// ===== Bluetooth =====
// Advertising set handle cấp bởi stack
static uint8_t advertising_set_handle = 0xFF;

// ===== GATT characteristic bạn đã tạo =====
#define AUDIO_RESULT_CHAR   gattdb_audio_result   // bạn nói ID = 21

// ===== GỬI KẾT QUẢ RA BLE =====
// Hàm này sẽ được audio-classifier.cc gọi mỗi khi có label mới
// Ghi giá trị vào GATT local DB rồi notify cho tất cả client đã enable
void app_ble_send_result(const char *label)
{
  if (label == NULL) {
    return;
  }

  // Giới hạn payload an toàn 20 byte nếu chưa MTU exchange
  // (Bạn có thể bỏ cắt nếu chắc MTU đã tăng)
  const uint16_t max_payload = 20;
  uint16_t len = (uint16_t)strlen(label);
  if (len > max_payload) len = max_payload;

  sl_status_t sc;

  // 1) Ghi attribute vào local GATT database (để client đọc thấy giá trị mới)
  sc = sl_bt_gatt_server_write_attribute_value(
        AUDIO_RESULT_CHAR,
        0,
        len,
        (const uint8_t *)label);
  app_log_status_error(sc);

  // 2) Gửi notification cho mọi client đã enable notify
  if (sc == SL_STATUS_OK) {
    sc = sl_bt_gatt_server_notify_all(
          AUDIO_RESULT_CHAR,
          len,
          (const uint8_t *)label);
    app_log_status_error(sc);

    if (sc == SL_STATUS_OK) {
      app_log_info("Audio result notified: %.*s" APP_LOG_NL, (int)len, label);
    }
  }
}

/******************************************************************************
 * Application Init.
 *****************************************************************************/
void app_init(void)
{
  // Khởi tạo pipeline ML (Micrium task + mic + model)
  audio_classifier_init();

  app_log_info("Audio+BLE app init." APP_LOG_NL);
}

/******************************************************************************
 * Application Process Action.
 * (Không cần làm gì ở đây; audio_classifier chạy bằng task riêng.)
 *****************************************************************************/
void app_process_action(void)
{
  // Bỏ trống. Audio classifier tự chạy theo RTOS task.
}

/******************************************************************************
 * Bluetooth stack event handler.
 *****************************************************************************/
void sl_bt_on_event(sl_bt_msg_t *evt)
{
  sl_status_t sc;

  switch (SL_BT_MSG_ID(evt->header)) {
    // -------------------------------
    // Boot: tạo advertiser và bắt đầu quảng cáo
    case sl_bt_evt_system_boot_id:
      // Create an advertising set
      sc = sl_bt_advertiser_create_set(&advertising_set_handle);
      app_assert_status(sc);

      // Generate advertising data (flags + name + services)
      sc = sl_bt_legacy_advertiser_generate_data(
            advertising_set_handle,
            sl_bt_advertiser_general_discoverable);
      app_assert_status(sc);

      // Set advertising interval = 100 ms (160 * 0.625 ms)
      sc = sl_bt_advertiser_set_timing(
            advertising_set_handle,
            160,  // min interval
            160,  // max interval
            0,    // duration
            0);   // max events
      app_assert_status(sc);

      // Start advertising (connectable)
      sc = sl_bt_legacy_advertiser_start(
            advertising_set_handle,
            sl_bt_legacy_advertiser_connectable);
      app_assert_status(sc);

      app_log_info("Advertising started." APP_LOG_NL);
      break;

    // -------------------------------
    case sl_bt_evt_connection_opened_id:
      app_log_info("Connection opened." APP_LOG_NL);
      break;

    // -------------------------------
    case sl_bt_evt_connection_closed_id:
      app_log_info("Connection closed." APP_LOG_NL);

      // Regen adv data (khuyến nghị của Silabs sau khi disconnect)
      sc = sl_bt_legacy_advertiser_generate_data(
            advertising_set_handle,
            sl_bt_advertiser_general_discoverable);
      app_assert_status(sc);

      // Restart advertising
      sc = sl_bt_legacy_advertiser_start(
            advertising_set_handle,
            sl_bt_legacy_advertiser_connectable);
      app_assert_status(sc);
      break;

    // -------------------------------
    // Tuỳ chọn: log khi client enable/disable notify trên AUDIO_RESULT_CHAR
    case sl_bt_evt_gatt_server_characteristic_status_id:
      if (evt->data.evt_gatt_server_characteristic_status.characteristic
          == AUDIO_RESULT_CHAR) {
        if (evt->data.evt_gatt_server_characteristic_status.status_flags
            == sl_bt_gatt_server_client_config) {
          if (evt->data.evt_gatt_server_characteristic_status.client_config_flags
              & sl_bt_gatt_notification) {
            app_log_info("audio_result notifications ENABLED." APP_LOG_NL);
          } else {
            app_log_info("audio_result notifications DISABLED." APP_LOG_NL);
          }
        }
      }
      break;

    // -------------------------------
    default:
      break;
  }
}
