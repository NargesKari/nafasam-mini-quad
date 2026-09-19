# Shopping list — one perfboard quadcopter controller

Buy the quantities below minus items you already own. “Buy” includes a few inexpensive spares; “fit” is the number used. **This replaces the bare-chip electronics shopping list for the prototype. Do not buy both sets for one build.** The original SMD version has a separate grouped list in ../shopping-list-original-PCB.md.

## Modules and motor switches

- [ ] **1 × Freenove FNK0085 ESP32-S3-WROOM camera board**, N8R8 or N16R8, with matching OV2640 camera and headers. Buy the board/camera bundle, without the large terminal expansion shield. No separate programmer, bare ESP32, flash, camera FPC connector or camera LDO is required. [Manufacturer](https://github.com/Freenove/Freenove_ESP32_S3_WROOM_Board).
- [ ] **1 × Adafruit MPU-6050 breakout with header pins**, fitted as U2. Supply VIN from 3.3 V. A GY-521 can be cheaper/local, but its regulator and pullups must be checked before substitution; see README. [Documented breakout](https://learn.adafruit.com/mpu6050-6-dof-accelerometer-and-gyro/pinouts).
- [ ] **1 × Pololu U3V40F5 fixed 5 V boost module**, U3. An alternative must deliver 5 V / 1 A from 3.0 V input, not merely advertise a 1 A or 2 A switch rating. [Reference module](https://www.pololu.com/product/4012).
- [ ] **8 × AO3400A MOSFETs**, fit 4 as Q1–Q4; reuse your existing parts if genuine and undamaged. SOT-23, gate pin1/source pin2/drain pin3. Buy pre-soldered adapters if you do not want to solder SMD.
- [ ] **4 × SOT-23-to-2.54 mm adapters**, preferably buy 6. Pick adapters with useful drain/source copper and short current paths. Generic tiny signal adapters are not automatically rated for 1.74 A motor operation; reinforce/test as described in README. If buying preassembled AO3400A adapters, the MOSFETs above are already included.
- [ ] **6 × 1N5822 axial Schottky diodes, 3 A / 40 V**, fit 4 as D1–D4. Banded end goes to battery positive. Do not substitute a 1N400x general-purpose rectifier or 1 A 1N5819 without redesign.

## Through-hole resistors — 1/4 W, preferably 1%

- [ ] **100 Ω: fit 4, buy 10** — R1–R4, series gate resistors.
- [ ] **10 kΩ: fit 4, buy 10** — R5–R8, gate-to-source pulldowns.
- [ ] **4.7 kΩ: fit 2, buy 5** — R9–R10, IMU I2C pullups to 3.3 V.
- [ ] **100 kΩ, 1%: fit 2, buy 5** — R11–R12, battery divider.

## Through-hole capacitors

- [ ] **100 nF (104), ceramic, X7R, 16 V or higher: fit 7, buy 10** — C1–C4 directly on motors; C12 at ESP 5 V; C13 on battery ADC; C14 at IMU supply. Radial leads, preferably 2.5 or 5 mm pitch.
- [ ] **10 µF, 10 V or higher, radial electrolytic: fit 5, buy 10** — C5–C8 driver supply bypass and C15 IMU bulk bypass. Choose compact parts; low ESR preferred. Match polarity.
- [ ] **47 µF, 10 V or higher, radial low-ESR electrolytic: fit 1, buy 2** — C10 at boost VIN.
- [ ] **100 µF, 10 V or higher, radial low-ESR electrolytic: fit 1, buy 2** — C11 at ESP 5 V input.
- [ ] **470 µF, 10 V, radial low-ESR electrolytic: fit 1, buy 2** — C9 at battery distribution. Choose a part with a published ripple-current rating of at least 1 A; verify temperature and rail ripple on the assembled prototype. Avoid large high-voltage substitutes that add unnecessary mass.

## Shared drone hardware — reuse what you have

- [ ] **4 × 8520 brushed coreless motors, nominal 3.7 V**, preferably a matched set of two CW and two CCW motors where the manufacturer specifies direction. Your stated running current is 1.74 A per motor; obtain or measure startup/stall current. No separate brushless ESCs are used.
- [ ] **1 × 1S 3.7 V 700 mAh 20C LiPo**, as already specified. Its label implies 14 A; verify real voltage sag and connector rating. A 2S battery is incompatible.
- [ ] **1 matching battery connector pair with short leads**, e.g. genuine XT30 if weight allows, or another connector with documented rating for the measured combined load. Do not assume a small JST-PH/Dupont connector can carry the four motors. If the pack already has a suitably rated connector, buy only its mating half. Confirm polarity with a meter.
- [ ] **1 × 1S LiPo charger**, correct 4.2 V termination and charge current permitted by your battery maker; 300–500 mA is a conservative starting choice only if allowed by the pack. Charging is off-board with the battery disconnected from the drone.
- [ ] **1 lightweight frame for four 8.5 mm diameter motors**, with room for the battery and perfboard. Check motor length, mounting method and total mass.
- [ ] **2 CW + 2 CCW matched propellers**, plus a spare set. Diameter, pitch and shaft fit must match the actual 8520 motors and frame; do not choose from “8520” alone.
- [ ] **Battery strap, insulating pad, wire strain relief and lightweight fasteners**, one small set. Use a secure IMU mount and check vibration; avoid a floppy module mounting.
- [ ] **Existing phone/computer for Wi-Fi commands and video**, plus compatible control firmware/software. No separate radio receiver is included in this Wi-Fi architecture.

## Perfboard and wiring

- [ ] **1 × 2.54 mm isolated-pad solderable perfboard**, about 60 × 80 mm starting size, thin double-sided plated board preferred. Trim after test fitting. This is برد سوراخ‌دار, not a solderless breadboard.
- [ ] **2 × 1×20 female socket strips, 2.54 mm**, for the selected 40-pin ESP board on the bench; check the actual header count/row spacing before soldering. Direct-solder or secure the connections for flight.
- [ ] **2 × 1×40 breakaway male header strips** and **1 × 1×40 female strip** to cut for sensor, regulator and adapters. Omit lengths already supplied/soldered on modules. High-current motor paths should use direct wires, not these sockets.
- [ ] **20 AWG flexible silicone wire, red/black: about 0.5 m of each** for short main battery/distribution wiring. Use 18 AWG if the run is longer or measured current demands it.
- [ ] **24 AWG flexible silicone wire: about 1 m total** for short motor branches; reuse adequate original motor leads.
- [ ] **28–30 AWG insulated signal wire: about 2 m total**, assorted colours; keep actual runs short.
- [ ] **Tinned copper bus wire around 0.8 mm diameter: about 0.5 m**, for short soldered power distribution, with insulation where it crosses other connections. Final current capability depends on length and temperature.
- [ ] **Heat-shrink assortment, solder, flux and insulation tape**, small quantities.
- [ ] **USB data cable matching the board** for programming. Disconnect the battery while using normal USB power.

## Bench equipment — borrow/reuse if available

- [ ] Soldering iron, cutters, tweezers and magnifier. An assembled AO3400A adapter avoids hand-soldering the SOT-23 package.
- [ ] Multimeter and current-limited bench supply. Test one motor at a time before whole-system load tests; supply and current measurement must cover the measured current.
- [ ] Scale with roughly 0.1 g resolution and a restrained thrust-test arrangement to establish flight weight/thrust margin.
- [ ] Oscilloscope access is useful for supply dips, PWM and I2C verification; it is test equipment, not an onboard component.

No flight duration, maximum lift or total price is promised: exact seller parts, propellers, available thrust and assembled mass are still unknown. Manufacturer links identify the reference parts; local availability and prices have not been checked.
