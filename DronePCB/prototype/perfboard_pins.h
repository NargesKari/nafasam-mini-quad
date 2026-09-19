#pragma once
// Freenove FNK0085 only. Header definitions, not flight firmware.
// Do not enable the SD card or external GPIO JTAG.
#define MOTOR1_GPIO 14
#define MOTOR2_GPIO 21
#define MOTOR3_GPIO 47
#define MOTOR4_GPIO 39
#define IMU_SDA_GPIO 41
#define IMU_SCL_GPIO 42
#define IMU_INT_GPIO 40
#define BATTERY_ADC_GPIO 1
#define BATTERY_DIVIDER_RATIO 2.0f
#define IMU_I2C_ADDRESS 0x68
// Camera pin profile: CAMERA_MODEL_ESP32S3_EYE in Freenove's camera example.
// Give camera XCLK and motor PWM separate LEDC timers/channels.
