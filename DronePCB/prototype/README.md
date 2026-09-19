# Drone perfboard prototype P1

This is a separate soldered **برد سوراخ‌دار** build. Open **Perfboard.kicad_pro** in KiCad. The original SMD PCB project is unchanged. The schematic has four circuit sheets plus an index. Matching net labels mean an electrical connection; the wire-list.md file lists every endpoint.

“MPU5060” is interpreted as the previously confirmed **MPU-6050**. Buy an assembled MPU-6050 breakout, not the bare QFN chip. This is a module/through-hole construction, not a literal all-DIP circuit: the ESP32 and MPU chips are already mounted on their modules, and AO3400A needs a SOT-23 adapter.

## Exact module choices

- **U1: Freenove ESP32-S3-WROOM camera board, FNK0085, N8R8 or N16R8, with its supplied compatible OV2640 and 2.54 mm headers.** Do not substitute the eight-pin-per-side AI-Thinker ESP32-CAM or a board with a different pinout. Use the supplied flex directly in the board camera socket. The board already contains camera power circuits, ESP32 decoupling, memory, boot/reset and USB programming circuitry.
- **U2: Adafruit MPU-6050 breakout**, powered at VIN = 3.3 V from U1. Its documented regulator and level shifting support this connection. Leave its 3Vo regulator-output pin unconnected. A GY-521 is a possible locally available substitute, but is not electrically standardized: first check its schematic, supply regulator and pullup rail. Do not simply put 5 V on its I2C pins. If powered at 3.3 V, verify the actual MPU VDD is within its 2.375–3.46 V operating range under load. The default drawing uses the Adafruit module.
- **U3: Pololu U3V40F5, fixed 5 V boost module.** It feeds only the electronics. If buying another boost module, require demonstrated 5 V / 1 A output from 3.0 V input, startup at or below 3.0 V, and acceptable ripple. An advertised switch/input-current number is not an output-current rating. The reference module is 15.2 × 15.2 mm and weighs 1.5 g. [Pololu specifications](https://www.pololu.com/product/4012).

For local sellers, useful search terms are «برد ESP32-S3 WROOM دوربین دار»، «ماژول MPU6050»، «تبدیل SOT23 به DIP»، «دیود شاتکی 1N5822» and «برد سوراخ دار دو طرفه 2.54 میلی متر». Product names alone do not establish matching pinouts.

## Signal wiring

The custom module symbols use printed **header labels as pin identifiers**. Their drawn positions and identifiers are not a footprint or sequential physical pin numbering. Use references/Freenove-pinout.png when finding the header pins.

- GPIO14 → R1 100 Ω → Q1 gate: motor 1.
- GPIO21 → R2 100 Ω → Q2 gate: motor 2.
- GPIO47 → R3 100 Ω → Q3 gate: motor 3.
- GPIO39 → R4 100 Ω → Q4 gate: motor 4.
- GPIO41 → IMU SDA. R9 4.7 kΩ pulls this line to 3.3 V.
- GPIO42 → IMU SCL. R10 4.7 kΩ pulls this line to 3.3 V.
- GPIO40 ← IMU INT. Configure and verify the IMU data-ready interrupt in firmware.
- IMU AD0 → GND, selecting address 0x68. IMU VIN → 3.3 V; IMU GND → common GND.
- GPIO1 ← battery divider midpoint: VBAT → R11 100 kΩ → midpoint → R12 100 kΩ → GND. C13 100 nF connects midpoint to GND. The nominal reading is half the battery voltage; calibrate ADC readings against a meter.

The camera's built-in connections occupy GPIO4–13 and GPIO15–18. GPIO39 and GPIO40 are normally associated with the SD socket, so **leave the SD socket empty and do not initialize SD**. Do not enable external GPIO JTAG on the reused pins. Boot straps, GPIO35–37 memory pins, USB GPIO19/20, UART GPIO43/44 and RGB LED GPIO48 are not assigned to motor outputs. The included header differs from the original custom PCB pin map.

The Adafruit board already has I2C pullups; the additional 4.7 kΩ resistors make a stronger effective pullup for short perfboard wiring. Start I2C at 100 kHz, check readings and rise times, then validate 400 kHz if required by the control-loop budget. Keep SDA/SCL short, with a nearby ground return.

## Power and each motor channel

Battery positive is **VBAT**, 3.0–4.2 V operating-test range for a 1S pack. Battery negative is GND. Motors connect directly to VBAT; never connect them to boosted 5 V or the ESP board power pins.

1. Battery + goes to each motor +, each diode's banded cathode, C9 positive and U3 VIN. Both VIN pads on the reference boost module may be wired in parallel.
2. Battery − goes to all four Q sources and, by a separate electronics return wire, U3 GND, U1 GND and IMU GND. Connect both GND pads on U3 where practical. Make the motor-current returns meet the battery return without flowing through the IMU/ESP ground wiring.
3. U3 VOUT goes to U1's **5V** pin. Leave U3 EN open; its onboard pullup enables it. U1's **3V3 output** supplies U2 and the I2C pullups.
4. For each AO3400A: **pin 1 = gate, pin 2 = source, pin 3 = drain**. Gate connects through the 100 Ω resistor to its PWM pin. Its 10 kΩ resistor connects gate directly to source. Drain connects to motor − and the diode's unbanded anode. Check adapter markings against the transistor pins with continuity testing; adapter header order is not universal.
5. D1–D4 are **1N5822, 3 A / 40 V Schottky**, band towards VBAT. Keep each diode and MOSFET loop short. The MOSFET's internal diode does not replace this flyback diode.
6. C1–C4, 100 nF ceramic, solder directly across the four motor terminals. C5–C8, 10 µF electrolytic, connect VBAT to GND near each driver; these are different connections from the motor capacitors.
7. C9, 470 µF low-ESR electrolytic, sits at the battery distribution point. C10, 47 µF, sits at U3 VIN. C11, 100 µF, and C12, 100 nF, sit at U1's 5 V input. C14, 100 nF, and C15, 10 µF, sit at U2 VIN. Observe electrolytic polarity.

Unplug the battery before connecting a normal USB cable for programming; this avoids unknown USB/external-supply backfeeding on board variants. Program with propellers removed. Disconnect USB before reconnecting the battery. There is no charging circuit, reverse-polarity protection or independent LiPo motor cutoff in this prototype. U3 EN does not completely disconnect its output. Unplug the battery after use.

## Perfboard construction

Use a 2.54 mm **isolated-pad** solderable perfboard, around 60 × 80 mm as a starting piece, trimmed after checking the actual module sizes. This is an arrangement guide rather than a hole-by-hole layout: module dimensions and SOT-23 adapters vary by seller. Never assume adjacent isolated pads are electrically connected. Stripboard requires a separate cut-track plan and is not the drawing's assumption.

Place the camera/ESP antenna at an outer edge, IMU close to the frame centre, and boost converter away from the IMU. Put the four motor drivers near their wire exit points. Position the battery bulk capacitor next to the main power junction. Keep battery, copper bus wires and carbon fibre away from the antenna. Mechanically secure modules and battery, add wire strain relief, and insulate the underside.

Use short 20 AWG silicone main battery wires (18 AWG for longer runs or higher measured currents), about 24 AWG for short individual motor branches, and 28–30 AWG for signals. Size the final wiring for measured startup current and acceptable voltage drop. Use soldered copper bus wire for motor distribution: **do not carry motor current through loose Dupont jumpers, solderless breadboards, thin adapter traces, or chains of perfboard solder bridges**. Inspect adapter copper and reinforce the drain/source routes as needed. Four motor currents total 6.96 A at the stated 1.74 A each, before electronics; stall current can be higher.

Sockets are convenient for bench changes. For flying, direct soldered module headers or properly secured sockets are preferable to loose plug-in leads. Reusing AO3400A on tiny adapters provides much less predictable cooling than the custom PCB, so temperature tests are necessary. At 1.74 A, the datasheet's 48 mΩ limit at 2.5 V gate drive implies about 0.145 W per FET at its reference temperature, before switching loss and hot-resistance increase. This is not a continuous-current approval for an adapter.

## Flight-test conditions

Perfboard can support prototyping and a restrained motor test. Flight capability cannot be established from the schematic: the development board, adapters, axial diodes, wiring and sockets add weight. Weigh the full aircraft and measure thrust with the actual propellers and battery; a total static thrust around twice takeoff weight is a useful design target for control margin, not a guarantee of stable flight.

Before flight, verify rails while all motors and camera/Wi-Fi operate, MOSFET/diode/connector temperatures, battery sag, IMU vibration response and motor directions. Begin electrically with motors disconnected, then test without propellers, followed by a restrained thrust test. Match two CW and two CCW propellers/motors to the frame and firmware mixer. Motor numbering here is electrical only; it does not assign frame corners or rotation directions.

Firmware must implement local stabilization, IMU calibration and axis mapping, an arming state, all-PWM-low startup, loss-of-link disarming, watchdog handling and battery monitoring. The motor timer/channel assignments must not overwrite the camera XCLK timer. Start with roughly 20 kHz motor PWM and validate heating/noise and firmware timing; tune if needed. The pin header supplied here is not flight-control software. A fresh cell reaches 4.2 V, so verify the motors' allowable supply and duty limits. Wi-Fi commands/video must not determine stabilization timing.

## Sources and checks

- [Freenove FNK0085 documentation](https://docs.freenove.com/projects/fnk0085/en/latest/fnk0085/codes/C/Preface.html)
- [Manufacturer pinout drawing](https://github.com/Freenove/Freenove_ESP32_S3_WROOM_Board/blob/main/ESP32S3_Pinout.png)
- [Manufacturer camera pin definitions](https://github.com/Freenove/Freenove_ESP32_S3_WROOM_Board/blob/main/C/Sketches/Sketch_07.1_CameraWebServer/camera_pins.h)
- [Adafruit MPU-6050 breakout pinouts](https://learn.adafruit.com/mpu6050-6-dof-accelerometer-and-gyro/pinouts)
- [TDK MPU-6050 specification](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet.pdf)
- [AO3400A specifications](https://www.aosmd.com/products/mosfets/low-voltage-mosfets-12v-30v/ao3400a)
- [Vishay 1N5822](https://www.vishay.com/en/product/88526/)

See validation.json for the schematic export/net comparison and ERC result. These checks verify the documented circuit's connections, not the wiring or performance of hardware assembled later. No routed PCB or automatic physical footprint mapping is supplied for this module-interface schematic.
