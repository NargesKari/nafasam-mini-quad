# nafasam-mini-quad

A phone-to-ESP32 wireless control link for a quadcopter, built around a hand-specified binary protocol with a checksum, a kill switch, and a failsafe — the network layer a drone project needs before the flight controller is worth writing.

## What it does

- Runs the ESP32 as a WiFi access point (`Drone-01`) serving a touch-control web page directly from flash, so any phone can connect with no app install.
- The web page renders two virtual joysticks (throttle/yaw, pitch/roll) and streams a 6-byte binary control packet over a WebSocket (`ws://192.168.4.1/ws`) at a fixed 50Hz, regardless of whether the sticks moved since the last tick.
- Defines a strict wire format (`docs/protocol.md`): throttle and the three axes as bytes 0-3, a flags bitmask (ARM / KILL / CALIBRATE / ACRO_MODE) as byte 4, and an XOR checksum as byte 5, with `KILL` documented to override every other field.
- Firmware validates the checksum on every packet and drops anything that doesn't match without touching control state or resetting the failsafe timer, and independently zeroes all outputs if no valid packet arrives for 300ms.
- `scripts/generate_web_header.py` regenerates the firmware's embedded HTML from the actual source file (`web/public/index.html`) instead of hand-editing a C string, so the control page has one source of truth.

## Why it's interesting

The protocol doc is written as the actual contract between three planned clients (webapp, future Android app, firmware) rather than being implicit in the code — it specifies not just the byte layout but the *reasoning*: why WebSocket-over-TCP was chosen for v1 despite the latency cost (browsers can't open raw UDP sockets), why the checksum exists even though TCP already guarantees integrity (it becomes load-bearing the moment the transport moves to UDP), and why control packets are sent unconditionally at 50Hz instead of only on change (a single dropped packet self-corrects in 20ms instead of leaving the drone stuck on stale input). That's the kind of protocol design that usually only shows up after a project has already been burned by not having it.

The current state is honest about what's actually flight-ready: `nafasam_quad.ino` receives, validates, and fails-safe on control packets correctly, but motor mixing and IMU calibration are explicit `TODO`s in the control loop — this is the wireless control link for a quadcopter, not yet a quadcopter that flies. That's a reasonable place to draw a v1 boundary: get the link layer's failure modes (dropped packets, corrupted packets, phone walking out of range, emergency stop) solid before writing flight-critical code on top of it.

## Tech stack

**Firmware:** C++ (Arduino framework) on ESP32, `ESPAsyncWebServer` + `AsyncTCP` for the async HTTP/WebSocket server.

**Control client:** Vanilla HTML/CSS/JS — dual touch joysticks, WebSocket client, connection-status indicator, portrait-lock overlay. No framework, no build step.

**Tooling:** Python 3 script to keep the firmware's embedded HTML in sync with its actual source file.

## Getting started

Build and flash the firmware with the Arduino IDE (needs the `ESPAsyncWebServer` and `AsyncTCP` libraries) targeting an ESP32 board — `firmware/nafasam_quad/nafasam_quad.ino` is the entry point.

If you edit the control page:

```bash
# edit web/public/index.html, then regenerate the firmware header
python3 scripts/generate_web_header.py
# re-flash firmware/nafasam_quad/nafasam_quad.ino
```

To fly (once motor mixing is implemented): connect a phone to the `Drone-01` WiFi network (password `drone1234`) and open `http://192.168.4.1/`.

## Architecture

`web/public/index.html` is the single source of truth for the control UI; `scripts/generate_web_header.py` compiles it into a `PROGMEM` C string (`firmware/nafasam_quad/web_page.h`) so the ESP32 can serve it without a filesystem. The firmware itself splits control-packet handling (an async WebSocket event callback that writes to `volatile` shared state) from the main loop (which reads that state, applies the kill/failsafe overrides, and will eventually drive the motors) — the two run on different execution contexts, which is why the shared variables are `volatile`.

<!-- add screenshot/demo here -->
