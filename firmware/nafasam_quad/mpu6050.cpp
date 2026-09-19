#include "mpu6050.h"

#define REG_CONFIG        0x1A
#define REG_GYRO_CONFIG   0x1B
#define REG_ACCEL_CONFIG  0x1C
#define REG_ACCEL_XOUT_H  0x3B
#define REG_PWR_MGMT_1    0x6B
#define REG_WHO_AM_I      0x75

#define ACCEL_LSB_PER_G   16384.0f   // +-2g
#define GYRO_LSB_PER_DPS  65.5f      // +-500 dps

bool Mpu6050::writeReg(uint8_t reg, uint8_t val) {
  _wire->beginTransmission(_addr);
  _wire->write(reg);
  _wire->write(val);
  return _wire->endTransmission() == 0;
}

bool Mpu6050::readRegs(uint8_t reg, uint8_t *buf, size_t len) {
  _wire->beginTransmission(_addr);
  _wire->write(reg);
  if (_wire->endTransmission(false) != 0) return false;
  if (_wire->requestFrom(_addr, (uint8_t)len) != len) return false;
  for (size_t i = 0; i < len; i++) buf[i] = _wire->read();
  return true;
}

bool Mpu6050::begin(TwoWire &wire, uint8_t addr) {
  _wire = &wire;
  _addr = addr;

  uint8_t who = 0;
  if (!readRegs(REG_WHO_AM_I, &who, 1)) return false;
  // 0x68 genuine; some clones report 0x70/0x72
  if (who != 0x68 && who != 0x70 && who != 0x72) {
    Serial.printf("MPU6050: unexpected WHO_AM_I 0x%02X\n", who);
    return false;
  }

  if (!writeReg(REG_PWR_MGMT_1, 0x80)) return false;   // reset
  delay(100);
  if (!writeReg(REG_PWR_MGMT_1, 0x01)) return false;   // wake, PLL on gyro X
  delay(10);
  if (!writeReg(REG_CONFIG, 0x03)) return false;       // DLPF ~44 Hz
  if (!writeReg(REG_GYRO_CONFIG, 0x08)) return false;  // +-500 dps
  if (!writeReg(REG_ACCEL_CONFIG, 0x00)) return false; // +-2 g
  return true;
}

bool Mpu6050::read(MpuData &out) {
  uint8_t b[14];
  if (!readRegs(REG_ACCEL_XOUT_H, b, sizeof(b))) return false;

  auto s16 = [&](int i) { return (int16_t)((b[i] << 8) | b[i + 1]); };
  out.ax = s16(0) / ACCEL_LSB_PER_G;
  out.ay = s16(2) / ACCEL_LSB_PER_G;
  out.az = s16(4) / ACCEL_LSB_PER_G;
  out.temp = s16(6) / 340.0f + 36.53f;
  out.gx = s16(8) / GYRO_LSB_PER_DPS;
  out.gy = s16(10) / GYRO_LSB_PER_DPS;
  out.gz = s16(12) / GYRO_LSB_PER_DPS;
  return true;
}
