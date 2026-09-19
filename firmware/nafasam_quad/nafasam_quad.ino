#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include "web_page.h"   // auto-generated from web/public/index.html

const char* AP_SSID = "Drone-01";
const char* AP_PASS = "drone1234"; // must be 8+ chars

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// ---- Shared control state (written from async TCP task, read in loop()) ----
volatile uint8_t g_throttle = 0;      // 0..255
volatile int16_t g_yaw = 0;           // -128..127 (data[1]-128)
volatile int16_t g_pitch = 0;         // -128..127
volatile int16_t g_roll = 0;          // -128..127
volatile uint8_t g_flags = 0;
volatile unsigned long g_lastPacketMillis = 0;
const unsigned long FAILSAFE_TIMEOUT_MS = 300;

// Flag bit positions
#define FLAG_ARM       0x01
#define FLAG_KILL      0x02
#define FLAG_CALIBRATE 0x04
#define FLAG_ACRO_MODE 0x08



void onWsEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
               AwsEventType type, void *arg, uint8_t *data, size_t len) {
  if (type == WS_EVT_CONNECT) {
    Serial.printf("Client #%u connected\n", client->id());
  } else if (type == WS_EVT_DISCONNECT) {
    Serial.printf("Client #%u disconnected\n", client->id());
    g_throttle = 0; g_yaw = 0; g_pitch = 0; g_roll = 0; g_flags = 0;
  } else if (type == WS_EVT_DATA) {
    if (len == 6) {
      uint8_t checksum = data[0] ^ data[1] ^ data[2] ^ data[3] ^ data[4];
      if (checksum != data[5]) {
        Serial.println("Checksum mismatch, packet dropped");
        return; // don't update state or lastPacketMillis -> failsafe will trigger if this persists
      }
      g_throttle = data[0];
      g_yaw   = (int16_t)data[1] - 128;
      g_pitch = (int16_t)data[2] - 128;
      g_roll  = (int16_t)data[3] - 128;
      g_flags = data[4];
      g_lastPacketMillis = millis();
    }
  }
}

void setup() {
  Serial.begin(115200);

  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("AP IP address: ");
  Serial.println(WiFi.softAPIP());

  ws.onEvent(onWsEvent);
  server.addHandler(&ws);

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send_P(200, "text/html", index_html);
  });

  server.begin();
}

unsigned long lastPrint = 0;

void loop() {
  ws.cleanupClients();

  // Failsafe: zero everything if no valid packet recently
  if (g_lastPacketMillis != 0 && millis() - g_lastPacketMillis > FAILSAFE_TIMEOUT_MS) {
    g_throttle = 0; g_yaw = 0; g_pitch = 0; g_roll = 0;
  }

  bool killed = g_flags & FLAG_KILL;
  bool calibrateRequested = g_flags & FLAG_CALIBRATE;
  bool armed = g_flags & FLAG_ARM;       // not driven by UI yet, reserved
  bool acroMode = g_flags & FLAG_ACRO_MODE; // not driven by UI yet, reserved

  if (calibrateRequested) {
    // TODO: tare/zero the MPU6050 here (drone must be flat and stationary)
    Serial.println("Calibrate gyro requested");
  }

  uint8_t finalThrottle = killed ? 0 : g_throttle;
  int16_t finalYaw   = killed ? 0 : g_yaw;
  int16_t finalPitch = killed ? 0 : g_pitch;
  int16_t finalRoll  = killed ? 0 : g_roll;

  // TODO: motor mixing goes here, using finalThrottle/finalYaw/finalPitch/finalRoll

  if (millis() - lastPrint > 200) {
    lastPrint = millis();
    Serial.printf("T:%d Y:%d P:%d R:%d  KILL:%d ARM:%d\n",
                  finalThrottle, finalYaw, finalPitch, finalRoll, killed, armed);
  }
}
