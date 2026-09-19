# nafasam-mini-quad

A phone-to-ESP32 wireless control link for a quadcopter, built around a hand-specified binary protocol with a checksum, a kill switch, and a failsafe — the network layer a drone project needs before the flight controller is worth writing.

## What it does

- Runs the ESP32 as an open WiFi access point (`nafasm`) serving a touch-control web page straight from flash, so any phone can connect with no app install.
- The page has two virtual joysticks (left: throttle/yaw, right: pitch/roll), an ARM/DISARM button, status lights (link / IMU / armed) and a help panel. It polls `GET /control` every 100 ms.
- A 200 Hz FreeRTOS task on core 0 reads the MPU6050 directly over its registers (no library), estimates roll/pitch with a complementary filter, runs PID stabilisation, mixes for an X-configuration quad and drives four transistor-switched brushed motors with PWM.
- Safety: failsafe disarm after 500 ms of silence, arm refused with throttle up, motors off on any IMU error, crash-angle disarm.

See `docs/protocol.md` for the exact contract.

## Repo layout

- `firmware/nafasam_quad/` - Arduino sketch (`.ino`, `config.h` pins/PID/safety, `mpu6050.*` driver, generated `web_page.h`)
- `web/public/index.html` - control page (single source of truth)
- `hardware/` - schematics, PCB, datasheets, mechanical parts
- `docs/` - protocol
- `scripts/generate_web_header.py` - embeds the page into the firmware

## Getting started

Arduino IDE with the ESP32 core v3.x (no extra libraries), open `firmware/nafasam_quad/nafasam_quad.ino`, select an ESP32 Dev Module, upload. Power the drone flat and still: the gyro calibrates at boot.

If you edit the control page:

```bash
python3 scripts/generate_web_header.py   # then re-flash
```

Connect to the `nafasm` WiFi and open `http://192.168.4.1/`.

**First power-up: remove the propellers** and check each motor's direction and the sign of the stabilisation on the bench before any flight.

<!-- add screenshot/demo here -->
