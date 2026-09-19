#pragma once

// ---------------- WiFi ----------------
#define AP_SSID        "nafasm"
#define AP_PASSWORD    ""          // empty = open network; otherwise 8+ chars

// ---------------- Pins ----------------
// I2C bus 0 (Wire) -> MPU6050
#define PIN_I2C_SDA    16          // board label RX2
#define PIN_I2C_SCL    17          // board label TX2
#define I2C_FREQ_HZ    100000      // weak pull-ups (~27k): keep at 100kHz
#define I2C_TIMEOUT_MS 5

// Motor transistor bases (PWM). Spin direction is fixed by wiring.
#define PIN_MOTOR_FL   23          // CW
#define PIN_MOTOR_FR   5           // CCW  (strapping pin: add a pull-down on the base)
#define PIN_MOTOR_RL   18          // CCW
#define PIN_MOTOR_RR   13          // CW

// ---------------- PWM ----------------
#define PWM_FREQ_HZ    1000
#define PWM_RES_BITS   10
#define PWM_MAX_DUTY   ((1 << PWM_RES_BITS) - 1)

// ---------------- Flight loop ----------------
#define LOOP_PERIOD_MS      5      // 200 Hz
#define FLIGHT_TASK_CORE    0
#define FLIGHT_TASK_PRIO    10
#define FLIGHT_TASK_STACK   6144

#define COMPLEMENTARY_ALPHA 0.98f  // gyro weight
#define MAX_TILT_DEG        25.0f  // full stick = this angle
#define MAX_YAW_RATE_DPS    120.0f // full stick = this yaw rate
#define CRASH_ANGLE_DEG     70.0f  // beyond this -> disarm

// ---------------- PID (output = fraction of full throttle) ----------------
#define KP_ANGLE        0.012f     // per degree of error
#define KI_ANGLE        0.008f     // per degree*second
#define KD_ANGLE        0.0015f    // per deg/s of measured rate
#define I_LIMIT         0.08f
#define KP_YAW_RATE     0.002f     // per deg/s of rate error
#define PID_OUT_LIMIT   0.35f
#define YAW_OUT_LIMIT   0.20f

// ---------------- Safety ----------------
#define FAILSAFE_MS         500    // no /control request for this long -> disarm
#define THROTTLE_DEADBAND   3      // % below which motors stay off
#define ARM_MAX_THROTTLE    5      // % - refuse to arm above this
#define IMU_FAIL_LIMIT      5      // consecutive read errors before re-init
#define IMU_RETRY_MS        500
