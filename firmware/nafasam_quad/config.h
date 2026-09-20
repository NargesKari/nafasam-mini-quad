#pragma once
#include <Arduino.h>

// ============================================================================
// Nafasam Mini Quad - Configuration & Hardware Pin Mapping
// Original PCB target: ESP32-S3-MINI-1-N4R2, DroneFC PCB Revision A0
// Pin map below is CUSTOMISED: motors 23/22/35/34, IMU 18/19/21
// Coreless Brushed Motors: 8520 (3.7V nominal, 1S LiPo)
// IMU: InvenSense MPU-6050 (QFN-24 bare chip on I2C address 0x68)
// ============================================================================

// ---------------- WiFi Access Point ----------------
#define AP_SSID             "Nafasam"
#define AP_PASSWORD         ""             // Empty = open network; otherwise 8+ chars
#define AP_CHANNEL          1
#define AP_MAX_CONN         4

// ---------------- I2C & IMU (MPU-6050) ----------------
// Custom wiring: IMU_SDA -> GPIO 18, IMU_SCL -> GPIO 19, IMU_INT -> GPIO 21
#define PIN_I2C_SDA         18
#define PIN_I2C_SCL         19
#define PIN_IMU_INT         21             // IMU INT (defined, not used by the firmware)
#define DRONE_IMU_I2C_ADDR  0x68           // MPU-6050 address
#define I2C_FREQ_HZ         400000         // 400 kHz Fast Mode
#define I2C_TIMEOUT_MS      10

// ---------------- Motors (8520 Brushed Coreless) ----------------
// Low-side AO3400A MOSFET switches on DroneFC PCB:
// Motor 1 (J4): Front-Left  (FL) - Clockwise (CW)          -> GPIO 23 (PWM1)
// Motor 2 (J5): Front-Right (FR) - Counter-Clockwise (CCW) -> GPIO 22 (PWM2)
// Motor 3 (J6): Rear-Left   (RL) - Counter-Clockwise (CCW) -> GPIO 35 (PWM3)
// Motor 4 (J7): Rear-Right  (RR) - Clockwise (CW)          -> GPIO 34 (PWM4)
//
// NOTE: on the classic ESP32, GPIO 34..39 are INPUT-ONLY (no PWM/output), and on
// the ESP32-S3 GPIO 22..25 do not exist. The firmware checks this at boot and
// refuses to arm if a motor pin cannot drive an output.
#define PIN_MOTOR_FL        23             // Motor 1 (J4)
#define PIN_MOTOR_FR        22             // Motor 2 (J5)
#define PIN_MOTOR_RL        35             // Motor 3 (J6)
#define PIN_MOTOR_RR        34             // Motor 4 (J7)

// ---------------- Motor PWM Settings ----------------
// High frequency PWM (16 kHz) eliminates audible coil whine and drives 8520 motors efficiently
#define PWM_FREQ_HZ         16000
#define PWM_RES_BITS        10             // 10-bit resolution (0..1023)
#define PWM_MAX_DUTY        ((1 << PWM_RES_BITS) - 1)
#define MOTOR_MAX_THROTTLE  0.95f          // 95% ceiling for voltage/thermal safety margin

// ---------------- Battery Monitoring ----------------
// DroneFC PCB: VBAT_SENSE on GPIO 1 through 100k / 100k voltage divider (2:1 ratio)
#define PIN_BATTERY_ADC     1
#define BATTERY_DIVIDER_RATIO 2.0f
#define BATTERY_LOW_VOLTS   3.30f          // Low battery warning threshold
#define BATTERY_CRIT_VOLTS  3.10f          // Critical battery threshold

// ---------------- Flight Loop (Core 0 FreeRTOS Task) ----------------
#define LOOP_PERIOD_MS      5              // 200 Hz control loop (5 ms)
#define FLIGHT_TASK_CORE    0
#define FLIGHT_TASK_PRIO    10
#define FLIGHT_TASK_STACK   8192

#define COMPLEMENTARY_ALPHA 0.98f          // Gyro weight in complementary filter
#define MAX_TILT_DEG        25.0f          // Full stick = 25 degrees tilt
#define MAX_YAW_RATE_DPS    150.0f         // Full stick = 150 deg/s yaw rate
#define CRASH_ANGLE_DEG     65.0f          // Tilt past this threshold triggers emergency disarm

// ---------------- PID Stabilisation Tuning ----------------
#define KP_ANGLE            0.014f         // Proportional gain per degree of error
#define KI_ANGLE            0.008f         // Integral gain per degree-second
#define KD_ANGLE            0.0020f        // Derivative gain per deg/s of gyro angular rate
#define I_LIMIT             0.08f          // Anti-windup limit for angle integral
#define KP_YAW_RATE         0.003f         // Proportional gain per deg/s of yaw rate error
#define PID_OUT_LIMIT       0.35f          // Max mixer contribution for roll/pitch PID
#define YAW_OUT_LIMIT       0.20f          // Max mixer contribution for yaw PID

// ---------------- Safety & Failsafes ----------------
#define FAILSAFE_MS         500            // Disarm after 500 ms of command silence
#define THROTTLE_DEADBAND   3              // Throttle % below which motors stay idle/off
#define ARM_MAX_THROTTLE    5              // Refuse arming if throttle exceeds 5%
#define IMU_FAIL_LIMIT      5              // Consecutive IMU read failures before failsafe
#define IMU_RETRY_MS        500            // IMU reconnection retry period