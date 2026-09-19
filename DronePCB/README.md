# DroneFC — engineering prototype A0

Open **design/DroneFC.kicad_pro** in KiCad 10. The project includes an editable seven-page schematic, a four-layer PCB, and local symbol/footprint libraries. The local libraries make the project portable.

**This is a prototype design, not a flight-tested or production-qualified controller. Read reports/validation-summary.json for the latest checks. Do not fabricate from an intermediate routing file.**

## Design choices

- ESP32-S3-MINI-1-N4R2: soldered module with 4 MB flash and 2 MB PSRAM. The module integrates RF circuitry and a PCB antenna. A bare ESP32 silicon implementation would require additional RF, clock and memory design.
- MPU-6050 bare QFN chip, I2C address 0x68. The auxiliary sensor bus and reserved pins are intentionally unused.
- Four AO3400A low-side motor switches, four SS34 flyback diodes, 100-ohm gate resistors, and 10-kilohm gate-to-source pulldowns.
- One 700 mAh, 20C, 1S LiPo. The advertised continuous discharge calculation is 0.7 Ah × 20 = 14 A; it does not establish the battery's real internal resistance or transient capability.
- TPS63021 fixed 3.3 V buck-boost converter for electronics, with a 1.5 uH inductor, two 10 uF input capacitors, three 22 uF output capacitors, and 100 nF control-supply bypass. Target electronics load is up to 1 A at battery voltage ≥3.0 V, subject to thermal/transient testing.
- TLV70028 and TLV70012 regulators provide the camera's 2.8 V and 1.2 V rails.
- A 10-ohm/1 uF filter feeds the IMU; local VDD, VLOGIC, REGOUT and CPOUT capacitors are 100 nF, 10 nF, 100 nF and 2.2 nF respectively. CPOUT uses a 50 V-rated capacitor.
- No charging circuit, SD card slot, USB socket, development-board headers, or flash LED. Programming uses solder pads and an external 3.3 V UART adapter.

## Mechanical and stackup intent

PCB outline: **50 × 50 mm**, nominal **0.8 mm** FR4, four copper layers. This is the first layout size, not a claim of minimum achievable size or mass. The antenna end of the ESP32 module extends beyond the PCB outline, so the assembled envelope is larger than 50 mm in that direction.

Layers: front signals/components, inner ground, inner battery distribution, back signals. Two camera signals (PCLK and RESET) also use the battery layer with clearance around them; the ground plane remains continuous. Ground and battery use solid connections to the inner planes. The motor-current pads use multiple vias. The final copper thickness, stackup, minimum spacing and via process must be agreed with the board manufacturer. The thermal/current assumptions require approximately 35 um finished copper on the power planes and outer layers; do not silently substitute thinner inner copper.

U2 uses the local TI_DSJ14_TPS63021 footprint, with a 1.58 × 2.85 mm exposed ground pad checked against TI drawing 4208549-3/E. Its peripheral lands are slightly enlarged relative to TI's example. Segmented paste covers approximately 65% of the exposed pad. Have the assembler qualify stencil thickness and via-in-pad treatment, including the module ground pads and the regulator ground connection. This is not a qualified assembly process.

Four M2 clearance holes use a nominal 44 × 26 mm spacing. Confirm that this pattern fits the frame. Keep the module antenna free of battery, carbon fibre, motors and wiring. The PCB is a controller mounted to a frame, not a structural motor-support plate.

## Camera compatibility

J3 uses **Hirose FH12-24S-0.5SH(55)**, a 24-pin, 0.5 mm pitch, bottom-contact FPC connector. Its electrical pinout follows the OV2640 interface shown in the AI-Thinker ESP32-CAM v1.6 reference schematic archived in references/ESP32_CAM_V1.6.pdf.

Buy only a camera flex assembly with this exact pinout. “OV2640” alone does not specify the connector pinout, contact side, flex thickness, lens clearance or power rails. The final camera assembly has not been selected from a seller. **The seller's flex drawing must be checked before fabrication.** The provided connector is not a generic plug for every ESP32 camera.

The camera's Y2–Y9 lines form D0–D7. Y0/Y1 and pin24 are unused. Camera I/O runs at 3.3 V, analog at 2.8 V and core at 1.2 V, consistent with the referenced assembly. See pin-map.json for the exact connections.

## Motor and battery connections

J2 pin1 is battery positive, pin2 is ground. J4–J7 pin1 is motor positive (VBAT), pin2 is the switched motor negative. SS34 cathodes connect to VBAT and anodes to motor negative. AO3400A pin1 is gate, pin2 source, pin3 drain.

**C101–C104 are off-board components:** solder one 100 nF, 16 V ceramic directly across each motor's terminals. Their presence in the BOM is intentional; they have no PCB footprints. C25–C28 are separate local 10 uF rail-decoupling capacitors near the motor drivers. C11 is a low-ESR 220 uF bulk capacitor. Its exact manufacturer part number, ripple rating, ESR and height remain a sourcing check; its allocated package is 6.3 × 5.8 mm.

The linked ECA listing describes 1.74 A as maximum loaded current. Four motors at that figure draw 6.96 A, excluding electronics. Stall/startup current is not specified by that figure. Measure it with current limiting and appropriate test equipment. Do not infer MOSFET, diode or battery stall survival from their headline current ratings.

AO3400A's specified 48 milliohm maximum at 2.5 V gate drive gives approximately 0.145 W conduction loss per motor at 1.74 A and continuous on-time at the datasheet reference temperature. Hot resistance, switching loss and flyback-diode dissipation increase the actual thermal load. This calculation is not a thermal qualification.

There is no reverse-polarity protection, battery charger or hardware LiPo cutoff on this board. Confirm polarity before connection, use an external 1S charger, and disconnect the battery after use. Battery voltage monitoring is available to firmware through a 100k/100k divider and 100 nF filter. The nominal ADC scale factor is 2, with calibration still required.

## Programming and firmware requirements

J1 pads, in order: GND, 3V3, UART_TX, UART_RX, BOOT, ESP_EN. Use **3.3 V logic**. Connect adapter TX to board RX and adapter RX to board TX. With the battery powering the board, use J1's 3V3 as a reference only; do not connect a second driven supply. Hold BOOT low while pulsing ESP_EN low to enter the ROM loader.

The included firmware header only defines hardware pins. It is not flight-control firmware. Before flying, implement and test local IMU sampling, calibration, attitude estimation, motor mixing, arming, link-loss response, watchdog response and low-battery handling. Flight stabilization must run locally; Wi-Fi carries commands/video rather than providing the timing of the stabilization loop. Keep camera processing from delaying the control loop.

All motor PWM outputs must initialize low. Establish a measured control-loop budget with camera streaming enabled. A fresh 1S cell reaches 4.2 V; the motors are listed as nominal 3.7 V. Confirm their permitted supply and use a battery-aware duty limit as appropriate. An average-voltage duty limit does not limit instantaneous stall current.

## Bench acceptance before flight

1. Inspect soldering and check supply resistance and polarity without battery connected. Start on a current-limited supply with motors disconnected.
2. Sweep battery input over the intended operating range and verify 3.3 V, 2.8 V, 1.2 V and IMU supply voltage, including camera/Wi-Fi transients.
3. Read MPU-6050 identity, check stationary gyro/accelerometer readings and confirm axis orientation. Check camera frames and the UART boot process.
4. With propellers removed, verify each motor remains off at boot/reset and test PWM individually. Then use a restrained thrust test to establish propeller load, startup current, voltage sag and component temperature.
5. Verify arming, loss-of-link response, watchdog reset and low-battery behavior before any flight. Establish thrust margin using the actual all-up mass.

## Sources

- [ESP32-S3-MINI module datasheet](https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.html)
- [Espressif camera driver and supported sensors](https://github.com/espressif/esp32-camera)
- [AI-Thinker ESP32-CAM v1.6 reference schematic, hosted by Seeed](https://github.com/SeeedDocument/forum_doc/blob/master/reg/ESP32_CAM_V1.6.pdf)
- [MPU-6000/6050 manufacturer specification](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet.pdf)
- [AO3400A manufacturer specifications](https://www.aosmd.com/products/mosfets/low-voltage-mosfets-12v-30v/ao3400a)
- [TPS63020/21 manufacturer datasheet](https://www.ti.com/lit/ds/symlink/tps63020.pdf)
- [XFL4020 inductor drawing](https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf)
- [Hirose camera connector](https://www.hirose.com/product/p/CL0586-0521-0-55)
- [ECA 8520 motor listing](https://eshop.eca.ir/موتور-coreless/6933-موتور-coreless-سایز-8520.html)

## Project contents

- design/DroneFC.kicad_pro, .kicad_sch and .kicad_pcb: editable KiCad project.
- BOM.csv: individual component values, packages and sourcing notes.
- design_manifest.json: component/net design intent; the PCB contains the final adjusted placement.
- pin-map.json and drone_pins.h: interface mapping.
- reports/: electrical, physical and connectivity checks.
- preview/: schematic and board previews.
- tools/ (working directory only, omitted from the delivery archive): development helpers and project-local routing tools. These contain intermediate design assumptions. Re-running build_design.py with --pcb replaces the board with its initial unrouted placement. Preserve the final PCB and local libraries before regenerating.

## Validation and delivery

The final routed PCB passes the configured KiCad electrical and physical checks with zero reported violations and zero unconnected items. An independent exported-netlist comparison matches all 240 connected component pins between schematic and PCB. The JSON reports list the checks that KiCad ignores under the project settings; a clean report does not establish thermal performance, signal integrity or flight suitability.

DroneFC-prototype-A0.zip contains the editable design, local libraries, component list, pin mapping, final reports and previews. No manufacturing release is included: camera flex compatibility, C11 sourcing, assembly process and manufacturer stackup still require confirmation. Actual motor startup/stall current, rail transients, thermal behavior and thrust margin require hardware tests. Board mass and efficiency have not been measured.
