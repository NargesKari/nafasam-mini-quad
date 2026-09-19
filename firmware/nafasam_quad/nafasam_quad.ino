// ============================================================================
// Nafasam Mini Quad - Flight Controller Firmware
// Hardware Target: ESP32-S3-MINI-1-N4R2, DroneFC PCB Revision A0
//
// Dual-Core FreeRTOS Architecture:
//   Core 0: 200 Hz Flight Control Loop (IMU read -> Fusion -> PID -> Mixer -> PWM)
//   Core 1: WiFi AP ("Nafasam") + esp_http_server (serves web UI, receives /control)
//
// Hardware Pinout (from DronePCB / drone_pins.h):
//   - Motor 1 (J4, Front-Left,  CW):  GPIO 39 (PWM1)
//   - Motor 2 (J5, Front-Right, CCW): GPIO 40 (PWM2)
//   - Motor 3 (J6, Rear-Left,   CCW): GPIO 41 (PWM3)
//   - Motor 4 (J7, Rear-Right,  CW):  GPIO 42 (PWM4)
//   - IMU I2C SDA:                    GPIO 33 (DroneFC IMU_SDA)
//   - IMU I2C SCL:                    GPIO 34 (DroneFC IMU_SCL)
//   - IMU INT:                        GPIO 21 (DroneFC IMU_INT)
//   - Battery Sense (100k/100k ADC):  GPIO 1  (DroneFC VBAT_SENSE)
//
// Sensor Alignment on DroneFC PCB:
//   PCB Top Edge (ESP32 antenna) = NOSE / FORWARD (+Y drone)
//   PCB Right Edge               = STARBOARD / RIGHT (+X drone)
//   PCB Bottom Edge (Camera FPC) = TAIL / REAR (-Y drone)
//   PCB Left Edge                = PORT / LEFT (-X drone)
//   MPU-6050 (U3) placed at center with rotation 0 (Pin 1 top-left):
//     - Chip +X points to Drone Right
//     - Chip +Y points to Drone Forward (Nose)
//     - Chip +Z points Up (out of the PCB top face)
//
// Angular / Axis Conventions:
//   - Roll:  Right side down = positive angle (Roll > 0).
//            Gravity component along chip -X. Gyro rate = +gy (around nose axis).
//   - Pitch: Nose down (stick forward) = positive angle (Pitch > 0).
//            Gravity component along chip -Y. Gyro rate = -gx (around pitch axis).
//   - Yaw:   Clockwise seen from above = positive yaw rate.
//            Gyro rate = -gz.
// ============================================================================

#include <WiFi.h>
#include <Wire.h>
#include <esp_http_server.h>
#include <math.h>

#include "config.h"
#include "mpu6050.h"
#include "web_page.h"   // Auto-generated from web/public/index.html

// ----------------------------------------------------------------------------
// Shared Thread-Safe Control Command State
// ----------------------------------------------------------------------------

struct ControlCmd {
  uint8_t  throttle;   // 0..100 %
  int8_t   yaw;        // -100..100 % (right = CW)
  int8_t   pitch;      // -100..100 % (forward = +)
  int8_t   roll;       // -100..100 % (right = +)
  bool     armed;      // Arm request from web UI
  uint32_t stamp;      // millis() timestamp of last received packet
};

static ControlCmd g_cmd = {0, 0, 0, 0, false, 0};
static portMUX_TYPE g_cmdMux = portMUX_INITIALIZER_UNLOCKED;

// Real-time telemetry indicators (monitored by HTTP server & loop)
static volatile bool  g_armedActive = false;   // Actual flight loop arming state
static volatile bool  g_imuOk       = false;   // IMU operational status
static volatile float g_dbgRoll     = 0.0f;    // Estimated roll angle (deg)
static volatile float g_dbgPitch    = 0.0f;    // Estimated pitch angle (deg)
static volatile float g_dbgMotor[4] = {0, 0, 0, 0}; // Output duty per motor (0..1)
static volatile float g_vbat        = 0.0f;    // Battery voltage (V)

// ----------------------------------------------------------------------------
// 8520 Motor Drivers (AO3400A Low-Side N-MOSFETs via LEDC PWM)
// ----------------------------------------------------------------------------

enum { M_FL = 0, M_FR = 1, M_RL = 2, M_RR = 3 };
static const uint8_t MOTOR_PINS[4] = {
  PIN_MOTOR_FL, // Motor 1: Front-Left  (CW)  -> GPIO 39
  PIN_MOTOR_FR, // Motor 2: Front-Right (CCW) -> GPIO 40
  PIN_MOTOR_RL, // Motor 3: Rear-Left   (CCW) -> GPIO 41
  PIN_MOTOR_RR  // Motor 4: Rear-Right  (CW)  -> GPIO 42
};

static inline float clampf(float v, float lo, float hi) {
  return (v < lo) ? lo : ((v > hi) ? hi : v);
}

// Drive all 4 motors with normalized duty cycle [0.0 .. 1.0]
static void motorsWrite(const float duty[4]) {
  for (int i = 0; i < 4; i++) {
    float v = clampf(duty[i], 0.0f, MOTOR_MAX_THROTTLE);
    g_dbgMotor[i] = v;
    uint32_t rawDuty = (uint32_t)(v * (float)PWM_MAX_DUTY);
    ledcWrite(MOTOR_PINS[i], rawDuty);
  }
}

// Cut all motor power immediately
static void motorsOff() {
  const float zeros[4] = {0.0f, 0.0f, 0.0f, 0.0f};
  motorsWrite(zeros);
}

// Configure GPIOs and attach LEDC PWM timers
static void motorsInit() {
  // CRITICAL HARDWARE SAFETY: Force all motor gate lines LOW before starting peripherals
  for (int i = 0; i < 4; i++) {
    pinMode(MOTOR_PINS[i], OUTPUT);
    digitalWrite(MOTOR_PINS[i], LOW);
  }

  // Attach ESP32-S3 LEDC PWM channels (Arduino ESP32 Core v3.x API)
  for (int i = 0; i < 4; i++) {
    ledcAttach(MOTOR_PINS[i], PWM_FREQ_HZ, PWM_RES_BITS);
  }

  motorsOff();
}

// ----------------------------------------------------------------------------
// Battery Voltage Monitor
// ----------------------------------------------------------------------------

static float readBatteryVoltage() {
  // ESP32-S3 calibrated ADC readout in millivolts
  uint32_t mv = analogReadMilliVolts(PIN_BATTERY_ADC);
  return (float)mv * BATTERY_DIVIDER_RATIO / 1000.0f;
}

// ----------------------------------------------------------------------------
// IMU (MPU-6050) & Sensor Alignment
// ----------------------------------------------------------------------------

static Mpu6050 mpu;

static const float RAD2DEG = 57.2957795f;

// Accelerometer attitude angles mapped specifically to DroneFC PCB orientation:
//   Chip +X = Right, Chip +Y = Nose, Chip +Z = Up
static inline float accelRoll(const MpuData &d) {
  // Rolling right causes gravity reaction vector to tilt left (-X)
  return atan2f(-d.ax, d.az) * RAD2DEG;
}

static inline float accelPitch(const MpuData &d) {
  // Pitching forward causes gravity reaction vector to tilt backwards (-Y)
  return atan2f(-d.ay, sqrtf(d.ax * d.ax + d.az * d.az)) * RAD2DEG;
}

// Initialize I2C bus and calibrate MPU-6050 on a flat surface
static bool imuStartup(ImuCal &cal) {
  Wire.end();
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_FREQ_HZ);
  Wire.setTimeOut(I2C_TIMEOUT_MS);

  if (!mpu.begin(Wire, DRONE_IMU_I2C_ADDR)) {
    Serial.println("MPU-6050: Connection failed! Check wiring on SDA:GPIO33, SCL:GPIO34");
    return false;
  }

  Serial.println("MPU-6050: Calibrating (Keep drone FLAT and STILL)...");

  const int SAMPLES = 300;
  double sumGyro[3] = {0.0, 0.0, 0.0};
  double sumRoll = 0.0;
  double sumPitch = 0.0;

  for (int i = 0; i < SAMPLES; i++) {
    MpuData d;
    if (!mpu.read(d)) {
      Serial.println("MPU-6050: Read failed during calibration");
      return false;
    }
    sumGyro[0] += d.gx;
    sumGyro[1] += d.gy;
    sumGyro[2] += d.gz;
    sumRoll    += accelRoll(d);
    sumPitch   += accelPitch(d);
    vTaskDelay(pdMS_TO_TICKS(3));
  }

  for (int i = 0; i < 3; i++) {
    cal.gyroBias[i] = (float)(sumGyro[i] / SAMPLES);
  }
  cal.rollOffset  = (float)(sumRoll  / SAMPLES);
  cal.pitchOffset = (float)(sumPitch / SAMPLES);

  // If gyro bias is abnormally large, the board was likely moving
  if (fabsf(cal.gyroBias[0]) > 25.0f || fabsf(cal.gyroBias[1]) > 25.0f || fabsf(cal.gyroBias[2]) > 25.0f) {
    Serial.println("MPU-6050: Calibration rejected (movement detected). Retrying...");
    return false;
  }

  Serial.printf("MPU-6050: Ready! Gyro Bias: X=%.2f Y=%.2f Z=%.2f dps | Trim: R=%.1f P=%.1f deg\n",
                cal.gyroBias[0], cal.gyroBias[1], cal.gyroBias[2],
                cal.rollOffset, cal.pitchOffset);
  return true;
}

// ----------------------------------------------------------------------------
// Core 0 FreeRTOS Flight Task (200 Hz Stabilisation & Motor Mixer)
// ----------------------------------------------------------------------------

static void flightTask(void *param) {
  (void)param;
  ImuCal cal = {};
  bool imuReady   = false;
  bool armed      = false;
  bool armLock    = false;   // Safety interlock: must see armed=0 before enabling arm
  uint8_t failCnt = 0;
  uint32_t lastRetryMs = 0;
  uint32_t lastLoopUs  = micros();

  float rollAngle  = 0.0f;
  float pitchAngle = 0.0f;
  float iRoll      = 0.0f;
  float iPitch     = 0.0f;

  TickType_t nextWakeTime = xTaskGetTickCount();

  for (;;) {
    vTaskDelayUntil(&nextWakeTime, pdMS_TO_TICKS(LOOP_PERIOD_MS));

    // 1. Ensure IMU is initialized and calibrated
    if (!imuReady) {
      motorsOff();
      g_imuOk = false;
      g_armedActive = false;
      armed = false;

      if (millis() - lastRetryMs >= IMU_RETRY_MS) {
        lastRetryMs = millis();
        imuReady = imuStartup(cal);
        if (imuReady) {
          rollAngle  = 0.0f;
          pitchAngle = 0.0f;
          iRoll      = 0.0f;
          iPitch     = 0.0f;
          failCnt    = 0;
          lastLoopUs = micros();
          g_imuOk    = true;
        }
      }
      continue;
    }

    // 2. Read IMU sensor data
    MpuData d;
    if (!mpu.read(d)) {
      motorsOff();
      g_armedActive = false;
      armed = false;
      armLock = true;
      if (++failCnt >= IMU_FAIL_LIMIT) {
        Serial.println("MPU-6050: Lost bus communication, resetting IMU");
        imuReady = false;
        lastRetryMs = 0;
      }
      continue;
    }
    failCnt = 0;

    // 3. Compute delta time
    uint32_t nowUs = micros();
    float dt = (float)(nowUs - lastLoopUs) * 1e-6f;
    lastLoopUs = nowUs;
    if (dt <= 0.0f || dt > 0.05f) {
      dt = (float)LOOP_PERIOD_MS * 1e-3f;
    }

    // 4. Map sensor axes to Drone Body Frame
    // On DroneFC PCB:
    //   Roll rate is rotation about Forward (+Y) axis: gy
    //   Pitch rate is rotation about Lateral (+X) axis: nose down is -gx
    //   Yaw rate is rotation about Vertical (+Z) axis: CW rotation is -gz
    float gyroRollRate  =  (d.gy - cal.gyroBias[1]);
    float gyroPitchRate = -(d.gx - cal.gyroBias[0]);
    float gyroYawRate   = -(d.gz - cal.gyroBias[2]);

    // 5. Sensor Fusion (Complementary Filter)
    float accR = accelRoll(d)  - cal.rollOffset;
    float accP = accelPitch(d) - cal.pitchOffset;

    rollAngle  = COMPLEMENTARY_ALPHA * (rollAngle  + gyroRollRate  * dt) + (1.0f - COMPLEMENTARY_ALPHA) * accR;
    pitchAngle = COMPLEMENTARY_ALPHA * (pitchAngle + gyroPitchRate * dt) + (1.0f - COMPLEMENTARY_ALPHA) * accP;

    g_dbgRoll  = rollAngle;
    g_dbgPitch = pitchAngle;

    // 6. Fetch latest control command snapshot (thread-safe)
    ControlCmd cmd;
    portENTER_CRITICAL(&g_cmdMux);
    cmd = g_cmd;
    portEXIT_CRITICAL(&g_cmdMux);

    // 7. Safety checks and failsafes
    // Check for link loss (timeout > 500 ms)
    bool linkActive = (cmd.stamp != 0) && ((millis() - cmd.stamp) < FAILSAFE_MS);
    if (!linkActive) {
      if (armed) armLock = true;
      cmd.armed    = false;
      cmd.throttle = 0;
    } else if (!cmd.armed) {
      armLock = false; // Disarmed from phone, reset lock
    }

    // Arming interlocks:
    // - Refuse to arm if throttle stick is raised (> 5%)
    // - Refuse to arm if drone is currently flipped (> 65 degrees)
    bool wantArm = cmd.armed && !armLock;
    if (wantArm && !armed && cmd.throttle > ARM_MAX_THROTTLE) {
      armLock = true;
      wantArm = false;
    }
    if (wantArm && (fabsf(rollAngle) > CRASH_ANGLE_DEG || fabsf(pitchAngle) > CRASH_ANGLE_DEG)) {
      armLock = true;
      wantArm = false;
    }

    armed = wantArm;
    g_armedActive = armed;

    // If disarmed or below throttle deadband, cut all motors
    if (!armed || cmd.throttle < THROTTLE_DEADBAND) {
      motorsOff();
      iRoll  = 0.0f;
      iPitch = 0.0f;
      continue;
    }

    // 8. Flight Control PID
    // Desired setpoints from web joystick commands:
    float spRoll    = (cmd.roll  / 100.0f) * MAX_TILT_DEG;
    float spPitch   = (cmd.pitch / 100.0f) * MAX_TILT_DEG;
    float spYawRate = (cmd.yaw   / 100.0f) * MAX_YAW_RATE_DPS;

    // Angle errors:
    float errRoll  = spRoll  - rollAngle;
    float errPitch = spPitch - pitchAngle;

    // Integrator with anti-windup:
    iRoll  = clampf(iRoll  + errRoll  * KI_ANGLE * dt, -I_LIMIT, I_LIMIT);
    iPitch = clampf(iPitch + errPitch * KI_ANGLE * dt, -I_LIMIT, I_LIMIT);

    // PID outputs (Derivative on measurement damping):
    float outRoll  = clampf(KP_ANGLE * errRoll  + iRoll  - KD_ANGLE * gyroRollRate,  -PID_OUT_LIMIT, PID_OUT_LIMIT);
    float outPitch = clampf(KP_ANGLE * errPitch + iPitch - KD_ANGLE * gyroPitchRate, -PID_OUT_LIMIT, PID_OUT_LIMIT);
    float outYaw   = clampf(KP_YAW_RATE * (spYawRate - gyroYawRate), -YAW_OUT_LIMIT, YAW_OUT_LIMIT);

    // 9. X-Configuration Motor Mixer for 8520 Brushed Motors:
    //   - FL (J4, Motor 1, CW):  base - pitch + roll - yaw
    //   - FR (J5, Motor 2, CCW): base - pitch - roll + yaw
    //   - RL (J6, Motor 3, CCW): base + pitch + roll + yaw
    //   - RR (J7, Motor 4, CW):  base + pitch - roll - yaw
    float baseThrottle = cmd.throttle / 100.0f;
    float motorPwm[4];

    motorPwm[M_FL] = baseThrottle - outPitch + outRoll - outYaw;
    motorPwm[M_FR] = baseThrottle - outPitch - outRoll + outYaw;
    motorPwm[M_RL] = baseThrottle + outPitch + outRoll + outYaw;
    motorPwm[M_RR] = baseThrottle + outPitch - outRoll - outYaw;

    motorsWrite(motorPwm);
  }
}

// ----------------------------------------------------------------------------
// Core 1 HTTP Server Handlers
// ----------------------------------------------------------------------------

static bool queryInt(const char *queryString, const char *key, int minVal, int maxVal, int &outVal) {
  char buf[16];
  if (httpd_query_key_value(queryString, key, buf, sizeof(buf)) != ESP_OK) return false;
  int v = atoi(buf);
  outVal = (v < minVal) ? minVal : ((v > maxVal) ? maxVal : v);
  return true;
}

// Serve touch controller web page
static esp_err_t handleRoot(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  httpd_resp_set_hdr(req, "Cache-Control", "no-cache, no-store, must-revalidate");
  return httpd_resp_send(req, index_html, HTTPD_RESP_USE_STRLEN);
}

// Handle periodic control polling: /control?throttle=..&yaw=..&pitch=..&roll=..&armed=..
static esp_err_t handleControl(httpd_req_t *req) {
  char query[128];
  int t = 0, y = 0, p = 0, r = 0, a = 0;

  if (httpd_req_get_url_query_str(req, query, sizeof(query)) != ESP_OK ||
      !queryInt(query, "throttle", 0, 100, t) ||
      !queryInt(query, "yaw", -100, 100, y) ||
      !queryInt(query, "pitch", -100, 100, p) ||
      !queryInt(query, "roll", -100, 100, r) ||
      !queryInt(query, "armed", 0, 1, a)) {
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Invalid control query");
    return ESP_OK;
  }

  // Update control state with atomic lock
  portENTER_CRITICAL(&g_cmdMux);
  g_cmd.throttle = (uint8_t)t;
  g_cmd.yaw      = (int8_t)y;
  g_cmd.pitch    = (int8_t)p;
  g_cmd.roll     = (int8_t)r;
  g_cmd.armed    = (a == 1);
  g_cmd.stamp    = millis();
  portEXIT_CRITICAL(&g_cmdMux);

  // Return telemetry JSON including IMU health, armed status, and battery voltage
  char body[64];
  snprintf(body, sizeof(body),
           "{\"armed\":%d,\"imu\":%d,\"vbat\":%.2f}",
           g_armedActive ? 1 : 0,
           g_imuOk ? 1 : 0,
           g_vbat);

  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, body, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t handleFavicon(httpd_req_t *req) {
  httpd_resp_set_status(req, "204 No Content");
  return httpd_resp_send(req, nullptr, 0);
}

// Redirect captive portal checks to main control interface
static esp_err_t handleCaptive(httpd_req_t *req) {
  httpd_resp_set_status(req, "302 Found");
  httpd_resp_set_hdr(req, "Location", "http://192.168.4.1/");
  return httpd_resp_send(req, nullptr, 0);
}

static void startWebServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.core_id     = 1;
  config.lru_purge_enable = true;

  httpd_handle_t server = nullptr;
  if (httpd_start(&server, &config) != ESP_OK) {
    Serial.println("Web Server: Initialization failed!");
    return;
  }

  httpd_uri_t uriRoot = { "/", HTTP_GET, handleRoot, nullptr };
  httpd_register_uri_handler(server, &uriRoot);

  httpd_uri_t uriControl = { "/control", HTTP_GET, handleControl, nullptr };
  httpd_register_uri_handler(server, &uriControl);

  httpd_uri_t uriFavicon = { "/favicon.ico", HTTP_GET, handleFavicon, nullptr };
  httpd_register_uri_handler(server, &uriFavicon);

  // Captive portal probes for iOS and Android
  httpd_uri_t uriHotspot = { "/hotspot-detect.html", HTTP_GET, handleRoot, nullptr };
  httpd_register_uri_handler(server, &uriHotspot);

  httpd_uri_t uriGen204 = { "/generate_204", HTTP_GET, handleCaptive, nullptr };
  httpd_register_uri_handler(server, &uriGen204);

  Serial.println("Web Server: Active on port 80");
}

// ----------------------------------------------------------------------------
// Arduino Setup & Loop
// ----------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("\n=============================================");
  Serial.println("   Nafasam Mini Quad - Flight Controller");
  Serial.println("   Hardware: ESP32-S3 DroneFC PCB Rev A0");
  Serial.println("=============================================");

  // 1. Initialize motor PWM pins (immediate LOW state for MOSFET safety)
  motorsInit();
  Serial.printf("Motors: Attached on GPIOs FL:%d FR:%d RL:%d RR:%d @ %d Hz\n",
                PIN_MOTOR_FL, PIN_MOTOR_FR, PIN_MOTOR_RL, PIN_MOTOR_RR, PWM_FREQ_HZ);

  // 2. Configure battery ADC input
  analogSetPinAttenuation(PIN_BATTERY_ADC, ADC_11db);
  g_vbat = readBatteryVoltage();
  Serial.printf("Battery: Initial voltage = %.2f V\n", g_vbat);

  // 3. Start WiFi Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, strlen(AP_PASSWORD) ? AP_PASSWORD : nullptr, AP_CHANNEL, 0, AP_MAX_CONN);
  WiFi.setSleep(false); // Lowest latency Wi-Fi

  Serial.print("WiFi AP started! SSID: \"");
  Serial.print(AP_SSID);
  Serial.print("\" | IP: http://");
  Serial.print(WiFi.softAPIP());
  Serial.println("/");

  // 4. Start HTTP Control Server on Core 1
  startWebServer();

  // 5. Launch high-priority Flight Task pinned to Core 0 (200 Hz)
  xTaskCreatePinnedToCore(
    flightTask,
    "flight_loop",
    FLIGHT_TASK_STACK,
    nullptr,
    FLIGHT_TASK_PRIO,
    nullptr,
    FLIGHT_TASK_CORE
  );
  Serial.println("Flight Task: Created on Core 0 (200 Hz)");
  Serial.println("Ready! Connect phone to 'Nafasam' Wi-Fi and open 192.168.4.1\n");
}

void loop() {
  // Read battery voltage periodically
  g_vbat = readBatteryVoltage();

  // Bench Diagnostics (printed at 2 Hz)
  Serial.printf("[TELEM] Bat:%.2fV | IMU:%s | Arm:%s | Roll:%5.1f Pitch:%5.1f | M1:%.2f M2:%.2f M3:%.2f M4:%.2f\n",
                g_vbat,
                g_imuOk ? "OK" : "NO",
                g_armedActive ? "ARMED" : "DISARM",
                g_dbgRoll, g_dbgPitch,
                g_dbgMotor[M_FL], g_dbgMotor[M_FR], g_dbgMotor[M_RL], g_dbgMotor[M_RR]);

  delay(500);
}
