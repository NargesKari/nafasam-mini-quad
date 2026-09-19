# hardware

Everything physical: circuits, PCBs, parts.

- `schematics/` - motor driver circuits, power distribution, ESP32 wiring (KiCad/Fritzing/PDF exports)
- `pcb/` - board layouts and Gerber files
- `datasheets/` - ESP32, IMU, transistor, motor, battery datasheets
- `mechanical/` - frame, motor mounts, 3D-printable parts (STL/STEP)

# Wiring guide

Board: generic **ESP32-WROOM-32 DevKit, 30 pins**. Pin names below are the labels printed on the board, with the GPIO number in brackets. The source of truth for pins is `firmware/nafasam_quad/config.h`.

## 1. ESP32 <-> MPU6050 (GY-521 module)

| MPU6050 pin | ESP32 pin (board label) | Notes |
|---|---|---|
| VCC | **3V3** | 3.3 V, not VIN |
| GND | **GND** | |
| SDA | **RX2** (GPIO16) | I2C data |
| SCL | **TX2** (GPIO17) | I2C clock |
| AD0 | GND (or leave open) | I2C address 0x68 |
| INT, XDA, XCL | not connected | unused |

Pull-ups: one resistor from **SDA (GPIO16) to 3V3** and one from **SCL (GPIO17) to 3V3**, between 2.2k and 10k ideally (27k also works at the 100 kHz the firmware uses). Many GY-521 modules already include pull-ups; adding external ones in parallel is fine.

Mount the module flat, chip facing up, with the module's **X axis pointing to the nose** and **Y to the left**. If it is mounted differently the stabilisation signs must be remapped in `flightTask()`.

## 2. ESP32 -> motor drivers (PWM outputs)

Each motor has its own transistor stage. The ESP32 pin goes to the transistor **base/gate through a resistor**.

| Motor | Position | Spin | ESP32 pin (board label) |
|---|---|---|---|
| FL | front-left | CW | **D23** (GPIO23) |
| FR | front-right | CCW | **D5** (GPIO5) |
| RL | rear-left | CCW | **D18** (GPIO18) |
| RR | rear-right | CW | **D13** (GPIO13) |

Per-motor circuit (low-side switch):

```
Battery + ----------------+----------------+
                          |                |
                       [Motor]        [Diode] (flyback, cathode to battery +)
                          |                |
                          +----------------+
                          |
                  collector/drain
ESP32 GPIO --[R base]-- base/gate      transistor
                  emitter/source
                          |
Battery - / common GND ---+
```

Also add:
- **Base/gate resistor** (about 1k for a BJT is typical; size it for your transistor and motor current) from GPIO to base/gate.
- **Pull-down** (about 10k) from base/gate to GND. This matters most on **GPIO5**, a boot-strapping pin that can pulse during boot and would briefly spin the motor.
- **Flyback diode** across every motor (anode on the transistor side). Without it the motor's voltage spikes can destroy the transistor and reset the ESP32.
- **Noise-filter capacitor** across each motor terminals (as planned; ceramic 100 nF is typical).
- Make sure each transistor can handle the motor's **stall current**, with margin.

Spin direction is fixed by how each motor is wired/mounted (the firmware never reverses a motor). If a motor spins the wrong way, swap its two motor wires.

## 3. Battery

The battery type is not fixed by the code, so pick the option that matches yours:

| Connection | Goes to |
|---|---|
| Battery **+** | motor **+** terminals (all four, via a fuse/switch ideally) and the ESP32 power input (see below) |
| Battery **-** | **ESP32 GND**, MPU6050 GND and all transistor emitters/sources |

**All grounds must be common** (battery -, ESP32 GND, MPU6050 GND, every transistor emitter). If they are not joined, the PWM signal has no reference and the motors will misbehave.

Powering the ESP32:
- Battery gives **about 5 V** (e.g. a 5 V regulator/boost stage, or USB power bank): connect to **VIN** (5 V) and GND.
- Battery is a **single 3.7 V LiPo**: the DevKit's on-board regulator needs about 5 V at VIN, so use a boost converter to 5 V into **VIN**, or a 3.3 V regulated supply into the **3V3** pin (bypasses the on-board regulator; never do both at once).
- Do **not** connect a battery above 6 V directly to VIN.
- Never connect USB and an external supply to VIN at the same time without a diode.

Motor current spikes can brown out the ESP32. Put a **large capacitor (about 470 uF or more)** across the battery rails near the ESP32 and, if resets still occur, a separate supply/regulator for the ESP32.

## 4. Quick checklist before first power-up

1. Remove the propellers.
2. Check continuity: MPU SDA -> GPIO16, SCL -> GPIO17, and each motor pin against the table above.
3. Confirm no short between battery + and -, and that all grounds are joined.
4. Power on with the drone flat and still (the gyro calibrates at boot); wait for the **IMU** light on the web page.
5. Connect to the `nafasm` WiFi, open `192.168.4.1`, and test each motor with low throttle before flying.
