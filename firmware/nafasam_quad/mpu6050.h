#pragma once
#include <Arduino.h>
#include <Wire.h>

struct MpuData {
  float ax, ay, az;   // g
  float gx, gy, gz;   // deg/s
  float temp;         // deg C
};

struct ImuCal {
  float gyroBias[3];   // Gyroscope zero-rate offsets [X, Y, Z]
  float rollOffset;    // Accelerometer roll zero trim at boot
  float pitchOffset;   // Accelerometer pitch zero trim at boot
};

// Minimal register-level MPU6050 driver (no external library).
class Mpu6050 {
public:
  bool begin(TwoWire &wire, uint8_t addr = 0x68);
  bool read(MpuData &out);

private:
  bool writeReg(uint8_t reg, uint8_t val);
  bool readRegs(uint8_t reg, uint8_t *buf, size_t len);

  TwoWire *_wire = nullptr;
  uint8_t _addr = 0x68;
};
