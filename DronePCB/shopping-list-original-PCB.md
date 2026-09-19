# Shopping list — original SMD PCB A0

This is the grouped parts list for the original custom PCB, **not** the perfboard prototype. Use prototype/shopping-list.md for the module build. Fit quantities are exact from BOM.csv; buy quantities include inexpensive spares. Reuse motors/battery and shared frame/propeller/charger/wiring items from the prototype shopping list. Do not purchase these bare-chip support circuits for the module version.

Before ordering the custom PCB parts, confirm the selected camera flex matches the documented J3 pinout and choose the exact low-ESR bulk capacitor. Connector pads J1/J2/J4-J7 are solder pads already on the PCB, not purchased headers. A 3.3 V logic USB-UART programmer is required for this original board.

- [ ] **ESP32-S3-MINI-1-N4R2 — fit 1; buy 1.** U1. Package: RF_Module:ESP32-S2-MINI-1. 4MB flash / 2MB PSRAM; module antenna extends beyond top board edge
- [ ] **10uF — fit 7; buy 9.** C1, C5, C6, C25, C26, C27, C28. Package: Capacitor_SMD:C_0603_1608Metric. X7R, 10V; use specified voltage where marked
- [ ] **100nF — fit 9; buy 11.** C2, C4, C7, C13, C15, C21, C22, C23, C24. Package: Capacitor_SMD:C_0402_1005Metric. X7R, 10V; use specified voltage where marked
- [ ] **10k — fit 8; buy 10.** R1, R2, R10, R11, R17, R18, R19, R20. Package: Resistor_SMD:R_0402_1005Metric. 1%, 0402
- [ ] **1uF — fit 6; buy 8.** C3, C12, C17, C18, C19, C20. Package: Capacitor_SMD:C_0402_1005Metric. X7R, 10V; use specified voltage where marked
- [ ] **100k — fit 2; buy 5.** R3, R4. Package: Resistor_SMD:R_0402_1005Metric. 1%, 0402
- [ ] **TPS63021DSJR — fit 1; buy 1.** U2. Package: Drone:TI_DSJ14_TPS63021. Fixed3.3V; power-save mode; 1A electronics design target at VBAT>=3.0V subject to bench testing
- [ ] **1.5uH XFL4020-152MEC — fit 1; buy 1.** L1. Package: Drone:XFL4020. Coilcraft reference inductor; confirm exact suffix and DCR at sourcing
- [ ] **22uF — fit 3; buy 5.** C8, C9, C10. Package: Capacitor_SMD:C_0805_2012Metric. X5R 10V; verify effective capacitance under DC bias
- [ ] **220uF 10V — fit 1; buy 5.** C11. Package: Capacitor_SMD:CP_Elec_6.3x5.8. Low ESR aluminum/polymer; ripple-current rating >=1A; final exact part depends on sourcing
- [ ] **MPU-6050 — fit 1; buy 1.** U3. Package: Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm. I2C address0x68; use genuine bare chip, orientation must be calibrated in firmware
- [ ] **10R — fit 1; buy 5.** R5. Package: Resistor_SMD:R_0402_1005Metric. 1%, 0402
- [ ] **10nF — fit 1; buy 5.** C14. Package: Capacitor_SMD:C_0402_1005Metric. X7R, 10V; use specified voltage where marked
- [ ] **2.2nF 50V — fit 1; buy 5.** C16. Package: Capacitor_SMD:C_0402_1005Metric. X7R 50V +/-10%; charge pump capacitor
- [ ] **4.7k — fit 4; buy 6.** R6, R7, R8, R9. Package: Resistor_SMD:R_0402_1005Metric. 1%, 0402
- [ ] **OV2640 flex / FH12-24S-0.5SH(55) — fit 1; buy 1.** J3. Package: Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal. ONLY pin-compatible 24pin0.5mm OV2640 flex; bottom-contact connector, confirm flex contact side/length before purchase
- [ ] **TLV70028DDCR — fit 1; buy 1.** U4. Package: Package_TO_SOT_SMD:SOT-23-5. 2.8V analog camera rail,200mA
- [ ] **TLV70012DDCR — fit 1; buy 1.** U5. Package: Package_TO_SOT_SMD:SOT-23-5. 1.2V core camera rail,200mA
- [ ] **33R — fit 1; buy 5.** R12. Package: Resistor_SMD:R_0402_1005Metric. Source series damping; tune with scope
- [ ] **AO3400A — fit 4; buy 5.** Q1, Q2, Q3, Q4. Package: Package_TO_SOT_SMD:SOT-23. SOT23 G1/S2/D3; verify stall current and heating with actual prop
- [ ] **100R — fit 4; buy 6.** R13, R14, R15, R16. Package: Resistor_SMD:R_0402_1005Metric. 1%, 0402
- [ ] **SS34 — fit 4; buy 5.** D1, D2, D3, D4. Package: Diode_SMD:D_SMA. 3A40V Schottky flyback; cathode pad1 to VBAT
- [ ] **100nF 16V motor-mounted — fit 4; buy 6.** C101, C102, C103, C104. Package: off-board radial ceramic at motor terminals. Solder directly across motor terminals; included in BOM, off-board

## Additional original-board items

- [ ] 1 × OV2640 flex camera assembly with the exact AI-Thinker v1.6 24-pin pinout and compatible contact side; the camera connector above does not include the sensor/lens assembly.
- [ ] 1 × USB-UART adapter using 3.3 V logic, plus programming wires; use the programming instructions in README.md.
- [ ] Custom four-layer PCB and appropriate stencil/assembly service or reflow tools; the bare QFN packages are not intended for direct perfboard installation.
- [ ] Four motors, battery and suitable connector, charger, frame, matched propellers, wiring and mechanical supplies: see the shared-hardware section of prototype/shopping-list.md.

Original BOM.csv remains the per-reference source of truth. Electrical passives must meet the voltage/dielectric notes; CPOUT is 2.2 nF / 50 V. Manufacturer part numbers for generic resistors/capacitors and C11 remain sourcing choices.
