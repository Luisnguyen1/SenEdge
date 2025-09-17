/***************************************************************************//**
 * @file
 * @brief Audio classifier application
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
#include "os.h"
#include "sl_power_manager.h"
#include "sl_status.h"
#include "sl_led.h"
#include "sl_simple_led_instances.h"
#include "audio_classifier.h"
#include "recognize_commands.h"
#include "config/audio_classifier_config.h"
#include "sl_tflite_micro_model.h"
#include "sl_tflite_micro_init.h"
#include "sl_ml_audio_feature_generation.h"
#include "sl_sleeptimer.h"
#include <cmath>
#include "app.h"   // <<== thêm để gọi app_ble_send_result()

#if SL_SIMPLE_LED_COUNT < 2
  #error "Sample application requires two leds"
#endif

// Pointer to RecognizeCommands object for handling recognitions.
static RecognizeCommands *command_recognizer = nullptr;

// Micrium OS Task variables
static OS_TCB tcb;
static CPU_STK stack[TASK_STACK_SIZE];

// Variables for detection/activity
static int32_t detected_timeout = 0;
static int32_t activity_timestamp = 0;
static int32_t activity_toggle_timestamp = 0;
static uint8_t previous_score = 0;
static int32_t previous_score_timestamp = 0;
static int previous_result = 0;

// Category label variables
int category_count = 0;
const char* category_labels[] = CATEGORY_LABELS;
static int category_label_count = sizeof(category_labels) / sizeof(category_labels[0]);

static void audio_classifier_task(void *arg);
static void handle_result(int32_t current_time, int result, uint8_t score, bool is_new_command);

static sl_status_t run_inference()
{
  sl_status_t status = sl_ml_audio_feature_generation_fill_tensor(sl_tflite_micro_get_input_tensor());
  if (status != SL_STATUS_OK){
    return SL_STATUS_FAIL;
  }
  TfLiteStatus invoke_status = sl_tflite_micro_get_interpreter()->Invoke();
  if (invoke_status != kTfLiteOk) {
    return SL_STATUS_FAIL;
  }
  return SL_STATUS_OK;
}

static sl_status_t process_output(){
  uint8_t result = 0;
  uint8_t score = 0;
  bool is_new_command = false;
  uint32_t current_time_stamp;
  sl_status_t status = SL_STATUS_OK;

  current_time_stamp = sl_sleeptimer_tick_to_ms(sl_sleeptimer_get_tick_count());

  TfLiteStatus process_status = command_recognizer->ProcessLatestResults(
      sl_tflite_micro_get_output_tensor(), current_time_stamp, &result, &score, &is_new_command);

  if (process_status == kTfLiteOk) {
    handle_result(current_time_stamp, result, score, is_new_command);
  } else {
    status = SL_STATUS_FAIL;
  }

  return status;
}

void audio_classifier_init(void)
{
  RTOS_ERR err;

  char task_name[] = "audio classifier task";
  OSTaskCreate(&tcb,
               task_name,
               audio_classifier_task,
               DEF_NULL,
               TASK_PRIORITY,
               &stack[0],
               (TASK_STACK_SIZE / 10u),
               TASK_STACK_SIZE,
               0u,
               0u,
               DEF_NULL,
               (OS_OPT_TASK_STK_CLR),
               &err);

  EFM_ASSERT((RTOS_ERR_CODE_GET(err) == RTOS_ERR_NONE));
}

void audio_classifier_task(void *arg)
{
  RTOS_ERR err;
  (void)&arg;

  printf("Audio Classifier\r\n");
  sl_ml_audio_feature_generation_init();
  
  static RecognizeCommands static_recognizer(sl_tflite_micro_get_error_reporter(), SMOOTHING_WINDOW_DURATION_MS,
      DETECTION_THRESHOLD, SUPPRESSION_TIME_MS, MINIMUM_DETECTION_COUNT, IGNORE_UNDERSCORE_LABELS);
  command_recognizer = &static_recognizer;

  const TfLiteTensor* input = sl_tflite_micro_get_input_tensor();
  const TfLiteTensor* output = sl_tflite_micro_get_output_tensor();

  if ((output->dims->size == 2) && (output->dims->data[0] == 1)) {
    category_count = output->dims->data[1];
  } else {
    printf("ERROR: Invalid output tensor shape\n");
    while (1);
  }

  if (category_count != category_label_count) {
    printf("WARNING: Number of categories(%d) != labels(%d)\n",
           category_count, category_label_count);
  }

  if ((input->type != kTfLiteInt8) || (output->type != kTfLiteInt8)) {
    printf("ERROR: Invalid tensor type.\n");
    while (1);
  }

  sl_power_manager_add_em_requirement(SL_POWER_MANAGER_EM1);

  while (1) {
    OSTimeDlyHMSM(0, 0, 0, INFERENCE_INTERVAL_MS, OS_OPT_TIME_PERIODIC, &err);
    EFM_ASSERT((RTOS_ERR_CODE_GET(err) == RTOS_ERR_NONE));

    sl_ml_audio_feature_generation_update_features();
    run_inference();
    process_output();
  }
}

static void handle_result(int32_t current_time, int result, uint8_t score, bool is_new_command) {
  const char *label = get_category_label(result);

  if (is_new_command) {
    printf("Detected class=%d label=%s score=%d @%ldms\n", result, label, score, current_time);

    // 🔹 Gửi kết quả qua BLE notify
    app_ble_send_result(label);

    // Điều khiển LED dựa trên nhãn
    if (result == 1) {
      sl_led_turn_on(&sl_led_led0);  // glass_breaking
      sl_led_turn_off(&sl_led_led1);
    } else {
      sl_led_turn_on(&sl_led_led1);  // noise
      sl_led_turn_off(&sl_led_led0);
    }

    detected_timeout = current_time + SUPPRESSION_TIME_MS;
  }

  if (detected_timeout == 0) {
    if (previous_score == 0) {
      previous_result = result;
      previous_score = score;
      previous_score_timestamp = current_time;
      return;
    }

    const int32_t time_delta = current_time - previous_score_timestamp;
    const int8_t score_delta = (int8_t)(score - previous_score);
    const float diff = (time_delta > 0) ? std::fabs(score_delta) / time_delta : 0.0f;

    previous_score = score;
    previous_score_timestamp = current_time;

    if (diff >= SENSITIVITY || (previous_result != result)) {
      previous_result = result;
      activity_timestamp = current_time + 500;
    } else if(current_time >= activity_timestamp) {
      activity_timestamp = 0;
      sl_led_turn_off(&ACTIVITY_LED);
    }

    if (activity_timestamp != 0) {
      if (current_time - activity_toggle_timestamp >= 100) {
        activity_toggle_timestamp = current_time;
        sl_led_toggle(&ACTIVITY_LED);
      }
    }
  }
}

const char * get_category_label(int index)
{
  if ((index >= 0) && (index < category_label_count)) {
    return category_labels[index];
  } else {
    return "?";
  }
}
