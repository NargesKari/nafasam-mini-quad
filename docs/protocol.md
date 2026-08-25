# Communication Protocol

Single source of truth for how phone-side controllers (webapp, Android app) talk to the ESP32 firmware. **Any client implementation (JS, Kotlin, firmware) must match this spec exactly.** If the packet format changes, update this file first, then update all three implementations.

Status: v1 — control channel only (phone → ESP32). No telemetry channel back yet.

---

## Transport

| Layer | Value |
|---|---|
| Network | ESP32 SoftAP (WiFi Access Point) |
| SSID | `Drone-01` |
| Password | `drone1234` |
| ESP32 IP | `192.168.4.1` (fixed, default SoftAP gateway address) |
| Protocol | WebSocket over TCP |
| Port | `80` |
| Path | `/ws` |
| Full URL | `ws://192.168.4.1/ws` |

WebSocket was chosen over plain HTTP polling because it's a persistent, low-overhead, bidirectional connection with no per-message handshake. TCP was chosen over UDP for v1 because it's directly usable from a browser (no raw sockets in JS); this is a known latency tradeoff — see **Future Changes** below.

---

## Send rate

Clients send a control packet **continuously at 50Hz (every 20ms)**, regardless of whether joystick values changed since the last tick. This is deliberate: if a single packet is dropped, the next one (20ms later) corrects the drone's state, rather than leaving it "stuck" on a stale command.

---

## Packet format (phone → ESP32)

6 bytes, sent as a single binary WebSocket frame.

| Byte | Name | Type | Range | Meaning |
|---|---|---|---|---|
| 0 | Throttle | `uint8` | 0–255 | 0 = no throttle, 255 = full throttle |
| 1 | Yaw | `uint8` | 0–255 | 128 = neutral/center, 0 = full left, 255 = full right |
| 2 | Pitch | `uint8` | 0–255 | 128 = neutral/center, 0 = full back, 255 = full forward |
| 3 | Roll | `uint8` | 0–255 | 128 = neutral/center, 0 = full left, 255 = full right |
| 4 | Flags | `uint8` (bitmask) | 0–255 | See Flags table below |
| 5 | Checksum | `uint8` | 0–255 | XOR of bytes 0–4 |

### Encoding throttle (unidirectional, 0–255)
```
byte = round( (normalizedValue + 1) / 2 * 255 )   // normalizedValue in -1..1, full stick travel
```
In practice throttle only uses the 0..1 half of stick travel in most client UIs, but the wire format always spans the full 0–255 range for consistency with the other axes.

### Encoding yaw / pitch / roll (bidirectional, centered at 128)
```
byte = round( (normalizedValue + 1) / 2 * 255 )   // normalizedValue in -1..1, where 0 = center
```
To recover a signed value on the receiving end (e.g. firmware):
```
signedValue = (int16_t)byte - 128   // range becomes -128..127, 0 = neutral
```

### Flags (byte 4, bitmask)

| Bit | Name | Meaning when set (1) |
|---|---|---|
| 0 | `ARM` | Motors armed. 0 = disarmed (motors must not spin regardless of stick input). |
| 1 | `KILL` | Emergency kill. Overrides everything — firmware must force all outputs to 0 immediately. |
| 2 | `CALIBRATE` | One-shot pulse: tare/zero the IMU. Client sends this as a single ~150ms pulse, not held. |
| 3 | `ACRO_MODE` | Flight mode toggle. 0 = auto-level (self-stabilizing), 1 = acro (rates only, no self-leveling). |
| 4–7 | *Reserved* | Unused. Must be sent as 0 until assigned a meaning here. |

**Precedence rule:** `KILL` always overrides `ARM`, throttle, and every other field — firmware checks this bit first, before doing anything else with the packet.

### Checksum (byte 5)
```
checksum = byte0 ^ byte1 ^ byte2 ^ byte3 ^ byte4
```
If the received checksum doesn't match, the firmware **must discard the packet** (do not update control state, do not reset the failsafe timer). This is currently redundant with TCP's own integrity guarantees, but becomes load-bearing if/when the transport moves to UDP (see below).

---

## Firmware-side failsafe

If no **valid** packet (correct checksum) is received for **300ms**, firmware must zero throttle/yaw/pitch/roll regardless of the last received values. This protects against WiFi drops, app crashes, or a phone walking out of range.

---

## Example packet

Throttle 50%, yaw centered, pitch full forward, roll centered, armed, not killed:

```
throttle = round(0.5 * 255)        = 128
yaw      = 128                      (center)
pitch    = 255                      (full forward)
roll     = 128                      (center)
flags    = 0b00000001 = 0x01        (ARM set, everything else 0)
checksum = 128 ^ 128 ^ 255 ^ 128 ^ 1 = 130

bytes: [128, 128, 255, 128, 1, 130]
```

---

## Future changes (not yet implemented — update this doc first if/when these land)

- **Telemetry channel (ESP32 → phone):** battery voltage, current attitude (from IMU), RSSI, armed/kill state confirmation. Will need its own message format, likely a different byte layout or a leading message-type byte to distinguish it from control packets if the channel is shared.
- **Move to UDP:** if WebSocket/TCP latency ever becomes noticeable in flight, migrating to raw UDP (via a native client, since browsers can't open raw UDP sockets) would remove TCP's head-of-line blocking. The checksum in this spec is already in place to make that transition safe.
- **Protocol version byte:** if the packet format changes in an incompatible way in the future, consider prepending a version byte so firmware can reject packets from an out-of-date client instead of silently misinterpreting them.

---

## Implementation checklist for a new client (e.g. the Android app)

- [ ] Connect to `Drone-01` WiFi network
- [ ] Open WebSocket to `ws://192.168.4.1/ws`
- [ ] Send a 6-byte binary frame every 20ms per the format above
- [ ] Compute checksum correctly (XOR of bytes 0–4)
- [ ] Implement KILL as a toggle that forces flags bit 1 on every subsequent packet until reset
- [ ] Implement CALIBRATE as a single-packet pulse, not held
- [ ] Handle WebSocket disconnect with automatic reconnect (matching webapp behavior)
