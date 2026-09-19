# Communication Protocol (v2)

Contract between the control page (`web/public/index.html`) and the ESP32 firmware. If this changes, update this file first, then both sides.

## Transport

| | |
|---|---|
| Network | ESP32 SoftAP, SSID `nafasm` (open by default, see `AP_PASSWORD` in `firmware/nafasam_quad/config.h`) |
| Address | `http://192.168.4.1` (port 80, `esp_http_server`) |

## Endpoints

### `GET /`
Serves the control page (embedded in flash as `web_page.h`).

### `GET /control?throttle=T&yaw=Y&pitch=P&roll=R&armed=A`

Sent by the page every 100 ms.

| Param | Range | Meaning |
|---|---|---|
| `throttle` | 0..100 | 0 = motors off |
| `yaw` | -100..100 | right = clockwise, commands a yaw *rate* (max 120 deg/s) |
| `pitch` | -100..100 | forward = +, commands an *angle* (max 25 deg) |
| `roll` | -100..100 | right = +, commands an *angle* (max 25 deg) |
| `armed` | 0/1 | requested arm state |

All five parameters are required; a missing one returns `400` and changes nothing. Values outside the range are clamped.

Response: `{"armed":0|1,"imu":0|1}` — the state the flight task is *actually* in (not the requested one) and whether the MPU6050 is working.

## Safety rules (enforced in firmware)

- **Failsafe:** no valid `/control` request for 500 ms → disarm and zero throttle. Re-arming then requires the page to send `armed=0` first.
- **Arm interlock:** arming is refused while `throttle > 5`; the page sees `armed:0` in the response and reverts the button.
- **IMU fault:** any MPU6050 read error turns all motors off immediately; after 5 consecutive errors the sensor is re-initialised and re-calibrated (board must be still).
- **Crash guard:** roll or pitch beyond 70 deg disarms.
- **Page hidden / closed:** the page disarms itself.
- Motors also stay off while `throttle < 3`.

## Flight loop (not part of the wire protocol)

200 Hz FreeRTOS task on core 0: MPU6050 registers over `Wire` → complementary filter (alpha 0.98) → PID on roll/pitch angle (D term from gyro rate) + P on yaw rate → X-configuration mixer → 1 kHz PWM via `ledcWrite`. Tunables are in `firmware/nafasam_quad/config.h`.

## Changes from v1

v1 used a 6-byte binary WebSocket frame at 50 Hz with an XOR checksum and KILL/CALIBRATE/ACRO flags. v2 replaces it with plain HTTP polling (no external async server library); KILL is now simply `armed=0`, and calibration happens automatically at boot.
