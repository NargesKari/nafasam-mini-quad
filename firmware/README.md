# firmware

ESP32 code. Open `nafasam_quad/nafasam_quad.ino` in the Arduino IDE (the folder name must match the `.ino` name).

- `nafasam_quad.ino` — WiFi AP, WebSocket control link, failsafe
- `web_page.h` — auto-generated from `web/public/index.html`; do not edit by hand (`python3 scripts/generate_web_header.py`)

Libraries: `ESPAsyncWebServer`, `AsyncTCP`.
