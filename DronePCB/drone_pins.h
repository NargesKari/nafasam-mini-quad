#pragma once
// Hardware mapping only. This file does not implement a flight controller.
// ESP32-S3-MINI-1-N4R2, DroneFC revision A0.
#define DRONE_MOTOR1_GPIO 39
#define DRONE_MOTOR2_GPIO 40
#define DRONE_MOTOR3_GPIO 41
#define DRONE_MOTOR4_GPIO 42
#define DRONE_BATTERY_ADC_GPIO 1
#define DRONE_IMU_SDA_GPIO 33
#define DRONE_IMU_SCL_GPIO 34
#define DRONE_IMU_INT_GPIO 21
#define DRONE_IMU_I2C_ADDRESS 0x68
#define DRONE_CAM_PWDN_GPIO 4
#define DRONE_CAM_RESET_GPIO (-1) // External RC pullup, no MCU reset line.
#define DRONE_CAM_SDA_GPIO 5
#define DRONE_CAM_SCL_GPIO 6
#define DRONE_CAM_XCLK_GPIO 7
#define DRONE_CAM_D0_GPIO 8
#define DRONE_CAM_D1_GPIO 9
#define DRONE_CAM_D2_GPIO 10
#define DRONE_CAM_D3_GPIO 11
#define DRONE_CAM_D4_GPIO 12
#define DRONE_CAM_D5_GPIO 13
#define DRONE_CAM_D6_GPIO 14
#define DRONE_CAM_D7_GPIO 15
#define DRONE_CAM_PCLK_GPIO 16
#define DRONE_CAM_HREF_GPIO 17
#define DRONE_CAM_VSYNC_GPIO 18
#define DRONE_UART_TX_GPIO 43
#define DRONE_UART_RX_GPIO 44
// Configure all motor outputs LOW before starting any peripherals.
// ADC division is nominally 2:1; calibrate against measured battery voltage.
