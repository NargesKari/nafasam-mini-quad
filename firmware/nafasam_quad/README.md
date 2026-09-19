# Nafasam Mini Quad - Firmware & Hardware Connection Guide

This directory contains the Arduino flight controller sketch for the **Nafasam Mini Quadcopter**, designed for the **ESP32-S3-MINI-1-N4R2** microcontroller and the **DroneFC PCB Revision A0**.

---

## 1. Physical Layout & Motor Orientation

The quadcopter uses an **X-Configuration**. The front of the drone corresponds to the top edge of the DroneFC PCB where the ESP32-S3 antenna extends.

```text
                  FRONT / NOSE
             (ESP32 Antenna Side)
                      ▲
                      │
     [Motor 1: FL]          [Motor 2: FR]
        GPIO 39                GPIO 40
        (CW ↻)                 (CCW ↺)
            \                /
             \    [U3]      /
              \  MPU-6050  /
               \  Center  /
                \        /
                 \      /
     [Motor 3: RL]          [Motor 4: RR]
        GPIO 41                GPIO 42
        (CCW ↺)                (CW ↻)
                      │
                      ▼
                 REAR / TAIL
            (Camera FPC Connector)
```

---

## 2. Complete Port & Pin Mapping Table

| Subsystem | Function / Signal | ESP32-S3 GPIO | PCB Net | Connector / Part Reference | Notes |
|---|---|---|---|---|---|
| **Motors (8520)** | Motor 1: Front-Left (FL) | **GPIO 39** | `PWM1` | `J4` / `Q1` (AO3400A) | Spin: Clockwise (**CW**). Switched to `MOTOR1_NEG`. |
| **Motors (8520)** | Motor 2: Front-Right (FR) | **GPIO 40** | `PWM2` | `J5` / `Q2` (AO3400A) | Spin: Counter-Clockwise (**CCW**). Switched to `MOTOR2_NEG`. |
| **Motors (8520)** | Motor 3: Rear-Left (RL) | **GPIO 41** | `PWM3` | `J6` / `Q3` (AO3400A) | Spin: Counter-Clockwise (**CCW**). Switched to `MOTOR3_NEG`. |
| **Motors (8520)** | Motor 4: Rear-Right (RR) | **GPIO 42** | `PWM4` | `J7` / `Q4` (AO3400A) | Spin: Clockwise (**CW**). Switched to `MOTOR4_NEG`. |
| **IMU (MPU-6050)** | I2C Serial Data (SDA) | **GPIO 33** | `IMU_SDA` | `U3` Pin 24 | Dedicated I2C bus with pull-up resistor. |
| **IMU (MPU-6050)** | I2C Serial Clock (SCL) | **GPIO 34** | `IMU_SCL` | `U3` Pin 23 | Dedicated I2C clock (400 kHz Fast-Mode). |
| **IMU (MPU-6050)** | Interrupt Line (INT) | **GPIO 21** | `IMU_INT` | `U3` Pin 12 | Active-high motion interrupt. |
| **Battery Monitor** | 1S LiPo Sense (ADC) | **GPIO 1** | `VBAT_SENSE` | `R2`/`R3` Voltage Divider | 100k / 100k divider (2:1 ratio). Max 4.2V $\rightarrow$ 2.1V at ADC. |
| **UART Programmer** | Transmit (TXD) | **GPIO 43** | `UART_TX` | `J1` Pad 3 | Connect to external 3.3V UART adapter **RX**. |
| **UART Programmer** | Receive (RXD) | **GPIO 44** | `UART_RX` | `J1` Pad 4 | Connect to external 3.3V UART adapter **TX**. |
| **UART Programmer** | Boot Mode Button/Pad | **GPIO 0** | `BOOT` | `J1` Pad 5 | Hold LOW while pulsing `ESP_EN` to flash. |
| **UART Programmer** | Chip Enable / Reset | `ESP_EN` | `ESP_EN` | `J1` Pad 6 | Pull LOW briefly to reset ESP32. |
| **Power Supply** | Main System 3.3V | `3V3` | `3V3` | `U2` (TPS63021) | Buck-boost converter output feeding ESP32 & sensors. |
| **Power Supply** | Common Ground | `GND` | `GND` | All GND pads | Ground plane common to battery, MCU, IMU, and MOSFET sources. |

---

## 3. Subsystem Wiring & Connection Details

### 3.1 8520 Coreless Brushed Motor Driver Circuit
Each motor is driven by a low-side AO3400A N-Channel MOSFET:
- **Gate**: Driven by ESP32-S3 GPIO via a $100\,\Omega$ series resistor (`R1`, `R18`, `R19`, `R20`), with a $10\,\text{k}\Omega$ pull-down to GND.
- **Drain**: Connects to the motor negative terminal (`MOTORx_NEG`).
- **Source**: Directly connected to solid board ground (`GND`).
- **Flyback Diode**: An SS34 Schottky diode is connected in parallel with each motor (Cathode to `VBAT`, Anode to `MOTORx_NEG`) to absorb inductive kickback spikes.
- **RF Noise Filter**: Solder a $100\,\text{nF}$, $16\,\text{V}$ ceramic capacitor (`C101`–`C104`) directly across the terminal wires of each 8520 motor.

### 3.2 InvenSense MPU-6050 IMU
- **I2C Address**: `0x68` (Pin `AD0` connected to `GND`).
- **Orientation on PCB**:
  - `+X` points to **Right**
  - `+Y` points to **Forward / Nose**
  - `+Z` points **Up**
- **Power**: Filtered `3V3` rail via a $10\,\Omega$ resistor and local decoupling capacitors ($100\,\text{nF}$ + $1\,\mu\text{F}$).

### 3.3 Battery Voltage Measurement
- Connect 1S LiPo battery positive terminal to `J2` Pin 1 (`VBAT`) and negative terminal to `J2` Pin 2 (`GND`).
- `VBAT_SENSE` routes through a 2:1 resistive voltage divider ($R_1 = 100\,\text{k}\Omega$, $R_2 = 100\,\text{k}\Omega$, filtered by a $100\,\text{nF}$ capacitor).
- Calculation in firmware:
  $$\text{Voltage} = \frac{\text{analogReadMilliVolts}(1) \times 2.0}{1000}$$

### 3.4 Programmer Pads (`J1`)
The board has a 6-pad programming interface for an external 3.3V USB-to-UART adapter:

```text
 Pad 1: GND      ─── Connect to Programmer GND
 Pad 2: 3V3      ─── Reference ONLY (Do NOT supply external power when battery is connected)
 Pad 3: UART_TX  ─── Connect to Programmer RX
 Pad 4: UART_RX  ─── Connect to Programmer TX
 Pad 5: BOOT     ─── Hold to GND while resetting to enter download mode
 Pad 6: ESP_EN   ─── Pull to GND briefly to reset the MCU
```

---

## 4. Arduino IDE Upload Instructions

1. Open `nafasam_quad.ino` in Arduino IDE 2.x.
2. Under **Tools $\rightarrow$ Board $\rightarrow$ esp32**, select **ESP32S3 Dev Module**.
3. Recommended settings:
   - **Flash Size**: `4MB (32Mb)`
   - **PSRAM**: `OPI PSRAM` (or Disabled if unused)
   - **Upload Speed**: `115200` or `921600`
   - **USB Mode**: `Hardware CDC and JTAG`
4. Connect programmer pads (`TX`, `RX`, `GND`). Hold `BOOT` low, pulse `ESP_EN` low, release `BOOT`, then click **Upload**.

---

## 5. First Flight Bench Acceptance Checklist

> [!CAUTION]
> **ALWAYS REMOVE ALL PROPELLERS** during bench testing and calibration!

1. **Visual & Continuity Inspection**:
   - Verify no short circuit between `VBAT` and `GND`.
   - Verify continuity on motor gate pins and IMU `SDA` (GPIO 33), `SCL` (GPIO 34).
2. **Boot IMU Calibration**:
   - Place the drone completely **flat and still** before applying battery power.
   - The gyro automatically averages 300 samples to establish bias offsets. The `IMU` indicator will turn green once calibration passes.
3. **Wi-Fi Connection**:
   - On your smartphone, connect to the Wi-Fi access point: **`Nafasam`** (open network).
   - Navigate to `http://192.168.4.1/`.
4. **Motor Spin Test**:
   - Arm the quad at zero throttle.
   - Slowly raise the throttle slider to verify all 4 motors spin.
   - Confirm proper rotation direction:
     - Motor 1 (FL): **Clockwise (CW)**
     - Motor 2 (FR): **Counter-Clockwise (CCW)**
     - Motor 3 (RL): **Counter-Clockwise (CCW)**
     - Motor 4 (RR): **Clockwise (CW)**
   - *If any motor spins in reverse, swap its two motor wire leads on the PCB.*
5. **Stabilisation Direction Check**:
   - With low throttle active, tilt the drone forward by hand: front motors should speed up to push the nose back up.
   - Tilt the drone to the right: right motors should speed up to level the frame.
