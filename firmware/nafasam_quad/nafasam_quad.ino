// nafasm quadcopter - ESP32 firmware
//
// Core 1: WiFi AP + esp_http_server (serves the control page, receives /control)
// Core 0: flight task @200 Hz (MPU6050 -> complementary filter -> PID -> X mixer -> PWM)
//
// Requires Arduino ESP32 core v3.x. No external libraries.
//
// Axis convention (MPU6050 mounted flat, chip facing up):
//   X -> nose, Y -> left, Z -> up.
// Angles: roll > 0 = right side down, pitch > 0 = nose down (stick forward).
// Yaw > 0 = clockwise seen from above. If your module is mounted differently,
// remap the axes where MpuData is read in flightTask().

#include <WiFi.h>
#include <Wire.h>
#include <esp_http_server.h>
#include <math.h>

#include "config.h"
#include "mpu6050.h"
#include "web_page.h"   // auto-generated from web/public/index.html

// ---------------------------------------------------------------- shared state

struct ControlCmd {
  uint8_t  throttle;   // 0..100
  int8_t   yaw;        // -100..100 (right = CW)
  int8_t   pitch;      // -100..100 (forward = +)
  int8_t   roll;       // -100..100 (right = +)
  bool     armed;
  uint32_t stamp;      // millis() of last valid request, 0 = never
};

static ControlCmd g_cmd = {0, 0, 0, 0, false, 0};
static portMUX_TYPE g_cmdMux = portMUX_INITIALIZER_UNLOCKED;

static volatile bool  g_armedActive = false;   // what the flight task is really doing
static volatile bool  g_imuOk = false;
static volatile float g_dbgRoll = 0, g_dbgPitch = 0;
static volatile float g_dbgMotor[4] = {0, 0, 0, 0};

// ---------------------------------------------------------------- motors

enum { M_FL, M_FR, M_RL, M_RR };
static const uint8_t MOTOR_PINS[4] = {PIN_MOTOR_FL, PIN_MOTOR_FR, PIN_MOTOR_RL, PIN_MOTOR_RR};

static void motorsWrite(const float f[4]) {
  for (int i = 0; i < 4; i++) {
    float v = f[i] < 0 ? 0 : (f[i] > 1 ? 1 : f[i]);
    g_dbgMotor[i] = v;
    ledcWrite(MOTOR_PINS[i], (uint32_t)(v * PWM_MAX_DUTY));
  }
}

static void motorsOff() {
  const float z[4] = {0, 0, 0, 0};
  motorsWrite(z);
}

static void motorsInit() {
  for (int i = 0; i < 4; i++) {
    ledcAttach(MOTOR_PINS[i], PWM_FREQ_HZ, PWM_RES_BITS);
  }
  motorsOff();
}

// ---------------------------------------------------------------- IMU

static Mpu6050 mpu;

struct ImuCal {
  float gyroBias[3];
  float rollOffset, pitchOffset;   // accel-angle offsets (level trim at boot)
};

static const float RAD2DEG = 57.29578f;

static inline float accelRoll(const MpuData &d)  { return atan2f(d.ay, d.az) * RAD2DEG; }
static inline float accelPitch(const MpuData &d) { return atan2f(-d.ax, sqrtf(d.ay * d.ay + d.az * d.az)) * RAD2DEG; }

// Bring up the bus + sensor and calibrate. Drone must be still and level.
static bool imuStartup(ImuCal &cal) {
  Wire.end();
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_FREQ_HZ);
  Wire.setTimeOut(I2C_TIMEOUT_MS);

  if (!mpu.begin(Wire)) return false;

  const int N = 300;
  double g[3] = {0, 0, 0}, r = 0, p = 0;
  for (int i = 0; i < N; i++) {
    MpuData d;
    if (!mpu.read(d)) return false;
    g[0] += d.gx; g[1] += d.gy; g[2] += d.gz;
    r += accelRoll(d); p += accelPitch(d);
    vTaskDelay(pdMS_TO_TICKS(3));
  }
  for (int i = 0; i < 3; i++) cal.gyroBias[i] = g[i] / N;
  cal.rollOffset = r / N;
  cal.pitchOffset = p / N;

  // Large bias means the board was moving during calibration: try again.
  if (fabsf(cal.gyroBias[0]) > 20 || fabsf(cal.gyroBias[1]) > 20 || fabsf(cal.gyroBias[2]) > 20) {
    Serial.println("IMU calibration rejected (board moving)");
    return false;
  }
  Serial.printf("IMU ready. gyro bias %.2f %.2f %.2f\n", cal.gyroBias[0], cal.gyroBias[1], cal.gyroBias[2]);
  return true;
}

// ---------------------------------------------------------------- flight task

static inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

static void flightTask(void *) {
  ImuCal cal = {};
  bool ready = false;
  bool armed = false;
  bool armLock = false;         // must see armed=0 from the phone before arming again
  uint8_t failCount = 0;
  uint32_t lastRetryMs = 0;
  uint32_t lastUs = micros();

  float roll = 0, pitch = 0;
  float iRoll = 0, iPitch = 0;

  TickType_t wake = xTaskGetTickCount();

  for (;;) {
    vTaskDelayUntil(&wake, pdMS_TO_TICKS(LOOP_PERIOD_MS));

    // ---- (re)initialise the IMU; motors stay off until it works ----
    if (!ready) {
      motorsOff();
      g_imuOk = false;
      g_armedActive = false;
      armed = false;
      if (millis() - lastRetryMs >= IMU_RETRY_MS) {
        lastRetryMs = millis();
        ready = imuStartup(cal);
        if (ready) {
          roll = pitch = 0;
          iRoll = iPitch = 0;
          failCount = 0;
          lastUs = micros();
          g_imuOk = true;
        } else {
          Serial.println("IMU init failed, retrying");
        }
      }
      continue;
    }

    // ---- read sensor ----
    MpuData d;
    if (!mpu.read(d)) {
      motorsOff();
      g_armedActive = false;
      armed = false;
      armLock = true;
      if (++failCount >= IMU_FAIL_LIMIT) {
        ready = false;
        lastRetryMs = 0;
      }
      continue;
    }
    failCount = 0;

    uint32_t nowUs = micros();
    float dt = (nowUs - lastUs) * 1e-6f;
    lastUs = nowUs;
    if (dt <= 0 || dt > 0.05f) dt = LOOP_PERIOD_MS * 1e-3f;

    float gx = d.gx - cal.gyroBias[0];        // roll rate
    float gy = d.gy - cal.gyroBias[1];        // pitch rate
    float yawRate = -(d.gz - cal.gyroBias[2]); // CW positive

    // ---- complementary filter ----
    roll  = COMPLEMENTARY_ALPHA * (roll  + gx * dt) + (1 - COMPLEMENTARY_ALPHA) * (accelRoll(d)  - cal.rollOffset);
    pitch = COMPLEMENTARY_ALPHA * (pitch + gy * dt) + (1 - COMPLEMENTARY_ALPHA) * (accelPitch(d) - cal.pitchOffset);
    g_dbgRoll = roll;
    g_dbgPitch = pitch;

    // ---- command snapshot + failsafe ----
    ControlCmd c;
    portENTER_CRITICAL(&g_cmdMux);
    c = g_cmd;
    portEXIT_CRITICAL(&g_cmdMux);

    bool linkOk = c.stamp != 0 && (millis() - c.stamp) < FAILSAFE_MS;
    if (!linkOk) {
      if (armed) armLock = true;
      c.armed = false;
      c.throttle = 0;
    } else if (!c.armed) {
      armLock = false;
    }

    bool wantArm = c.armed && !armLock;
    if (wantArm && !armed && c.throttle > ARM_MAX_THROTTLE) {
      armLock = true;   // refuse to arm with throttle up
      wantArm = false;
    }
    if (wantArm && (fabsf(roll) > CRASH_ANGLE_DEG || fabsf(pitch) > CRASH_ANGLE_DEG)) {
      armLock = true;   // flipped / crashed
      wantArm = false;
    }
    armed = wantArm;
    g_armedActive = armed;

    if (!armed || c.throttle < THROTTLE_DEADBAND) {
      motorsOff();
      iRoll = iPitch = 0;
      continue;
    }

    // ---- PID ----
    float spRoll  = c.roll  / 100.0f * MAX_TILT_DEG;
    float spPitch = c.pitch / 100.0f * MAX_TILT_DEG;
    float spYaw   = c.yaw   / 100.0f * MAX_YAW_RATE_DPS;

    float eRoll = spRoll - roll;
    float ePitch = spPitch - pitch;

    iRoll  = clampf(iRoll  + eRoll  * KI_ANGLE * dt, -I_LIMIT, I_LIMIT);
    iPitch = clampf(iPitch + ePitch * KI_ANGLE * dt, -I_LIMIT, I_LIMIT);

    float outRoll  = clampf(KP_ANGLE * eRoll  + iRoll  - KD_ANGLE * gx, -PID_OUT_LIMIT, PID_OUT_LIMIT);
    float outPitch = clampf(KP_ANGLE * ePitch + iPitch - KD_ANGLE * gy, -PID_OUT_LIMIT, PID_OUT_LIMIT);
    float outYaw   = clampf(KP_YAW_RATE * (spYaw - yawRate), -YAW_OUT_LIMIT, YAW_OUT_LIMIT);

    // ---- X-configuration mixer ----
    // FL CW, FR CCW, RL CCW, RR CW.
    // Pitch fwd: front down / rear up. Roll right: right down / left up.
    // Yaw CW: CCW motors (FR, RL) speed up, CW motors slow down (reaction torque).
    float base = c.throttle / 100.0f;
    float m[4];
    m[M_FL] = base - outPitch + outRoll - outYaw;
    m[M_FR] = base - outPitch - outRoll + outYaw;
    m[M_RL] = base + outPitch + outRoll + outYaw;
    m[M_RR] = base + outPitch - outRoll - outYaw;
    motorsWrite(m);
  }
}

// ---------------------------------------------------------------- HTTP

static bool queryInt(const char *q, const char *key, int lo, int hi, int &out) {
  char buf[12];
  if (httpd_query_key_value(q, key, buf, sizeof(buf)) != ESP_OK) return false;
  int v = atoi(buf);
  out = v < lo ? lo : (v > hi ? hi : v);
  return true;
}

static esp_err_t handleRoot(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, index_html, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t handleControl(httpd_req_t *req) {
  char q[96];
  int t, y, p, r, a;
  if (httpd_req_get_url_query_str(req, q, sizeof(q)) != ESP_OK ||
      !queryInt(q, "throttle", 0, 100, t) ||
      !queryInt(q, "yaw", -100, 100, y) ||
      !queryInt(q, "pitch", -100, 100, p) ||
      !queryInt(q, "roll", -100, 100, r) ||
      !queryInt(q, "armed", 0, 1, a)) {
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "bad query");
    return ESP_OK;
  }

  portENTER_CRITICAL(&g_cmdMux);
  g_cmd.throttle = t;
  g_cmd.yaw = y;
  g_cmd.pitch = p;
  g_cmd.roll = r;
  g_cmd.armed = a;
  g_cmd.stamp = millis();
  portEXIT_CRITICAL(&g_cmdMux);

  char body[48];
  snprintf(body, sizeof(body), "{\"armed\":%d,\"imu\":%d}", g_armedActive ? 1 : 0, g_imuOk ? 1 : 0);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, body, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t handleFavicon(httpd_req_t *req) {
  httpd_resp_set_status(req, "204 No Content");
  return httpd_resp_send(req, nullptr, 0);
}

static void startWebServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = 80;
  cfg.core_id = 1;
  cfg.lru_purge_enable = true;

  httpd_handle_t server = nullptr;
  if (httpd_start(&server, &cfg) != ESP_OK) {
    Serial.println("httpd_start failed");
    return;
  }

  httpd_uri_t root = {};
  root.uri = "/";
  root.method = HTTP_GET;
  root.handler = handleRoot;
  httpd_register_uri_handler(server, &root);

  httpd_uri_t control = {};
  control.uri = "/control";
  control.method = HTTP_GET;
  control.handler = handleControl;
  httpd_register_uri_handler(server, &control);

  httpd_uri_t fav = {};
  fav.uri = "/favicon.ico";
  fav.method = HTTP_GET;
  fav.handler = handleFavicon;
  httpd_register_uri_handler(server, &fav);
}

// ---------------------------------------------------------------- Arduino entry

void setup() {
  Serial.begin(115200);

  motorsInit();   // outputs low as early as possible

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, strlen(AP_PASSWORD) ? AP_PASSWORD : nullptr);
  WiFi.setSleep(false);
  Serial.print("AP \"" AP_SSID "\" IP: ");
  Serial.println(WiFi.softAPIP());

  startWebServer();

  xTaskCreatePinnedToCore(flightTask, "flight", FLIGHT_TASK_STACK, nullptr,
                          FLIGHT_TASK_PRIO, nullptr, FLIGHT_TASK_CORE);
}

void loop() {
  Serial.printf("imu:%d armed:%d roll:%6.1f pitch:%6.1f  FL:%.2f FR:%.2f RL:%.2f RR:%.2f\n",
                g_imuOk, g_armedActive, g_dbgRoll, g_dbgPitch,
                g_dbgMotor[M_FL], g_dbgMotor[M_FR], g_dbgMotor[M_RL], g_dbgMotor[M_RR]);
  delay(500);
}
