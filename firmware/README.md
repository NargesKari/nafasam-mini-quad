# firmware

ESP32-S3 firmware for the Nafasam Mini Quadcopter.

- [`nafasam_quad/`](nafasam_quad/): Arduino sketch directory. Open [`nafasam_quad/nafasam_quad.ino`](nafasam_quad/nafasam_quad.ino) in Arduino IDE.
- [`nafasam_quad/README.md`](nafasam_quad/README.md): **Hardware pinout and port connection guide** for ESP32-S3, MPU-6050, motors, battery ADC, and programmer.
- [`nafasam_quad/config.h`](nafasam_quad/config.h): Tunable flight control, PID, PWM, and Wi-Fi constants.
- [`nafasam_quad/web_page.h`](nafasam_quad/web_page.h): Auto-generated web interface header (regenerate with `python3 scripts/generate_web_header.py`).

No external Arduino libraries required (uses native ESP32 core v3.x: `WiFi`, `Wire`, `esp_http_server`).
